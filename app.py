import os
import sys
import shutil
import subprocess
import tempfile
import threading
import uuid
import hashlib
import io
from flask import (
    Flask, render_template, request, redirect, url_for,
    jsonify, Response, send_file
)
import pillow_heif
pillow_heif.register_heif_opener()
from PIL import Image, ImageFile, ImageOps
ImageFile.LOAD_TRUNCATED_IMAGES = True
import db
from auth import get_icloud_api, AuthRequired, TwoFactorRequired
from pyicloud.exceptions import PyiCloudFailedLoginException
from config import TRIAGE_DIR, ARCHIVE_DIR, FOR_DELETION_DIR

app = Flask(__name__)
app.secret_key = os.urandom(24)

db.init_db()

# Ensure triage folders exist
for _d in (TRIAGE_DIR, ARCHIVE_DIR, FOR_DELETION_DIR):
    os.makedirs(_d, exist_ok=True)

# Active subprocess streams: stream_id -> subprocess.Popen
_streams = {}


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

EXEMPT_ROUTES = {"setup", "setup_verify", "static"}

@app.before_request
def require_credentials():
    if request.endpoint in EXEMPT_ROUTES:
        return
    if db.get_credentials() is None or not db.is_auth_complete():
        return redirect(url_for("setup"))


# ---------------------------------------------------------------------------
# Index — unified triage page
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("triage.html")


# ---------------------------------------------------------------------------
# Setup / Auth
# ---------------------------------------------------------------------------

@app.route("/setup", methods=["GET", "POST"])
def setup():
    error = None
    needs_2fa = False

    if request.method == "POST":
        apple_id = request.form.get("apple_id", "").strip()
        password = request.form.get("password", "").strip()

        if not apple_id or not password:
            error = "Apple ID and password are required."
        else:
            db.save_credentials(apple_id, password)
            try:
                get_icloud_api()
                db.set_auth_complete()
                return redirect(url_for("index"))
            except TwoFactorRequired:
                needs_2fa = True
            except AuthRequired as e:
                error = str(e)

    return render_template("setup.html", error=error, needs_2fa=needs_2fa)


@app.route("/setup/verify", methods=["POST"])
def setup_verify():
    code = request.form.get("code", "").strip()
    if not code:
        return render_template("setup.html", error="Code is required.", needs_2fa=True)

    try:
        import pyicloud
        creds = db.get_credentials()
        cookie_dir = os.path.expanduser("~/Pictures/icloud-triage/app-data/cookies")
        api = pyicloud.PyiCloudService(
            creds["apple_id"], creds["password"], cookie_directory=cookie_dir
        )
        result = api.validate_2fa_code(code)
        if not result:
            return render_template("setup.html", error="Invalid code. Try again.", needs_2fa=True)
        db.set_auth_complete()
        return redirect(url_for("index"))
    except Exception as e:
        return render_template("setup.html", error=str(e), needs_2fa=True)


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.route("/settings")
def settings():
    creds = db.get_credentials()
    apple_id = creds["apple_id"] if creds else ""
    return render_template("settings.html", apple_id=apple_id)


@app.route("/settings/re-auth", methods=["POST"])
def settings_re_auth():
    db.clear_session()
    db.save_credentials("", "")
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    conn.execute("DELETE FROM credentials")
    conn.commit()
    conn.close()
    return redirect(url_for("setup"))


# ---------------------------------------------------------------------------
# Asset index sync
# ---------------------------------------------------------------------------

@app.route("/sync-index", methods=["POST"])
def sync_index():
    stream_id = str(uuid.uuid4())
    proc = subprocess.Popen(
        [sys.executable, "downloader.py", "--sync"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    _streams[stream_id] = proc
    return jsonify({"stream_id": stream_id})


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------

@app.route("/stream/<stream_id>")
def stream(stream_id):
    proc = _streams.get(stream_id)
    if not proc:
        return Response("data: {\"error\": \"unknown stream\"}\n\n", mimetype="text/event-stream")

    def generate():
        for line in proc.stdout:
            text = line.decode(errors="replace").rstrip()
            if text:
                yield f"data: {text}\n\n"
        proc.wait()
        _streams.pop(stream_id, None)
        yield "event: done\ndata: {}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


# ---------------------------------------------------------------------------
# Photo serving
# ---------------------------------------------------------------------------

THUMB_DIR = os.path.expanduser("~/Pictures/icloud-triage/app-data/thumbs")
THUMB_SIZE = (400, 400)
VIDEO_EXTENSIONS = {".mov", ".mp4", ".m4v", ".avi", ".mkv", ".3gp"}


def _thumb_path(asset_id):
    safe = hashlib.md5(asset_id.encode()).hexdigest()
    return os.path.join(THUMB_DIR, f"{safe}.jpg")


def _make_thumb(asset_id, local_path):
    os.makedirs(THUMB_DIR, exist_ok=True)
    thumb_path = _thumb_path(asset_id)
    ext = os.path.splitext(local_path)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
            result = subprocess.run(
                ["ffmpeg", "-y", "-ss", "0", "-i", local_path,
                 "-vframes", "1",
                 "-vf", f"scale={THUMB_SIZE[0]}:{THUMB_SIZE[1]}:force_original_aspect_ratio=decrease",
                 tmp_path],
                capture_output=True, timeout=30,
            )
            if result.returncode == 0 and os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 0:
                os.replace(tmp_path, thumb_path)
                tmp_path = None
        except Exception:
            pass
        finally:
            if tmp_path and os.path.isfile(tmp_path):
                os.unlink(tmp_path)
    else:
        try:
            img = Image.open(local_path)
            img = ImageOps.exif_transpose(img)
            img.thumbnail(THUMB_SIZE)
            img = img.convert("RGB")
            img.save(thumb_path, "JPEG", quality=80)
        except Exception:
            pass
    return thumb_path if os.path.isfile(thumb_path) else None


@app.route("/photo/<path:asset_id>")
def photo(asset_id):
    asset = db.get_asset(asset_id)
    if not asset or not asset["local_path"]:
        return "", 404
    path = asset["local_path"]
    if not os.path.isfile(path):
        return "", 404
    return send_file(path)


@app.route("/thumb/<path:asset_id>")
def thumb(asset_id):
    thumb_path = _thumb_path(asset_id)
    if not os.path.isfile(thumb_path):
        asset = db.get_asset(asset_id)
        if not asset or not asset["local_path"] or not os.path.isfile(asset["local_path"]):
            return "", 404
        thumb_path = _make_thumb(asset_id, asset["local_path"])
        if not thumb_path:
            return "", 404
    return send_file(thumb_path, mimetype="image/jpeg")


# ---------------------------------------------------------------------------
# Triage API
# ---------------------------------------------------------------------------

def _resolve_path(folder, filename):
    base, ext = os.path.splitext(filename)
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return path
    counter = 2
    while True:
        candidate = os.path.join(folder, f"{base}_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def _delete_from_icloud_async(asset_ids):
    """Background thread: delete assets from iCloud with early-exit scan."""
    try:
        from deleter import delete_single_asset
        api = get_icloud_api()
        remaining = set(asset_ids)
        photo_map = {}
        for photo in api.photos.all:
            if photo.id in remaining:
                photo_map[photo.id] = photo
                remaining.discard(photo.id)
            if not remaining:
                break
        for asset_id in asset_ids:
            photo = photo_map.get(asset_id)
            if photo:
                try:
                    photo.delete()
                except Exception:
                    pass
    except Exception:
        pass


@app.route("/api/triage/current")
def api_triage_current():
    assets = db.get_in_triage_assets()
    return jsonify(assets)


@app.route("/api/triage/start", methods=["POST"])
def api_triage_start():
    """Load the first batch or resume after restart."""
    in_triage = db.get_in_triage_assets()
    if in_triage:
        # Resuming after page/server reload — spawn a preload if no subprocess is
        # actually running (_streams is empty means nothing is actively downloading)
        stream_id = _spawn_download() if not _streams else None
        return jsonify({"triage_assets": in_triage, "stream_id": stream_id})

    # Promote downloading_next if ready
    downloading = db.get_downloading_next_assets()
    # Only promote if all expected assets have a local_path (download complete)
    ready = [a for a in downloading if a.get("local_path") and os.path.isfile(a["local_path"])]
    if ready:
        db.set_status_in_triage([a["id"] for a in ready])
        # Spawn next background download
        stream_id = _spawn_download()
        return jsonify({"triage_assets": ready, "stream_id": stream_id})

    # Nothing ready — spawn first download
    if downloading:
        # Still downloading, return empty and the stream will update progress
        return jsonify({"triage_assets": [], "stream_id": None, "status": "downloading"})

    stream_id = _spawn_download()
    return jsonify({"triage_assets": [], "stream_id": stream_id})


def _spawn_download():
    """Spawn background downloader subprocess. Returns stream_id or None."""
    if not db.get_eligible_batch_asset_ids():
        return None
    stream_id = str(uuid.uuid4())
    proc = subprocess.Popen(
        [sys.executable, "downloader.py", "--download"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    _streams[stream_id] = proc
    return stream_id


@app.route("/api/triage/top-up", methods=["POST"])
def api_triage_top_up():
    """Promote any newly-ready downloading_next assets into in_triage.
    Called when a background download completes while a triage batch is already showing."""
    downloading = db.get_downloading_next_assets()
    ready = [a for a in downloading if a.get("local_path") and os.path.isfile(a["local_path"])]
    if not ready:
        return jsonify({"new_assets": []})
    db.set_status_in_triage([a["id"] for a in ready])
    return jsonify({"new_assets": ready})


@app.route("/api/triage/next", methods=["POST"])
def api_triage_next():
    """Process current batch decisions and advance the pipeline."""
    data = request.get_json() or {}
    decisions = data.get("decisions", {})  # {asset_id: "lock"|"trash"|null}

    errors = []
    kept = 0
    archived = 0
    deleted_count = 0
    to_delete_ids = []

    for asset_id, decision in decisions.items():
        asset = db.get_asset(asset_id)
        if not asset:
            errors.append(f"Asset {asset_id} not found")
            continue

        src_path = asset.get("local_path")
        if not src_path or not os.path.isfile(src_path):
            errors.append(f"Source file missing for {asset.get('filename', asset_id)}")
            continue

        filename = os.path.basename(src_path)

        if decision == "lock":
            # Keep in iCloud + save to archive
            dest_path = _resolve_path(ARCHIVE_DIR, filename)
            try:
                shutil.copy2(src_path, dest_path)
                os.remove(src_path)
                db.set_status_keep_forever(asset_id, dest_path)
                kept += 1
            except Exception as e:
                errors.append(f"Failed to move {filename}: {e}")

        elif decision == "trash":
            dest_path = _resolve_path(FOR_DELETION_DIR, filename)
            try:
                shutil.copy2(src_path, dest_path)
                os.remove(src_path)
                # Verify local copy before scheduling iCloud delete
                if os.path.isfile(dest_path) and os.path.getsize(dest_path) > 0:
                    db.set_status_for_deletion(asset_id, dest_path)
                    to_delete_ids.append(asset_id)
                    deleted_count += 1
                else:
                    errors.append(f"Copy of {filename} is missing or zero bytes — iCloud delete skipped")
            except Exception as e:
                errors.append(f"Failed to move {filename}: {e}")

        else:  # "archive" or null fallback — save to archive + delete from iCloud
            dest_path = _resolve_path(ARCHIVE_DIR, filename)
            try:
                shutil.copy2(src_path, dest_path)
                os.remove(src_path)
                # Verify local copy before scheduling iCloud delete
                if os.path.isfile(dest_path) and os.path.getsize(dest_path) > 0:
                    db.set_status_archive(asset_id, dest_path)
                    to_delete_ids.append(asset_id)
                    archived += 1
                else:
                    errors.append(f"Copy of {filename} is missing or zero bytes — iCloud delete skipped")
            except Exception as e:
                errors.append(f"Failed to move {filename}: {e}")

    # Fire iCloud deletions in background thread (non-blocking)
    if to_delete_ids:
        t = threading.Thread(
            target=_delete_from_icloud_async,
            args=(to_delete_ids,),
            daemon=True,
        )
        t.start()

    # Promote downloading_next → in_triage
    downloading = db.get_downloading_next_assets()
    ready = [a for a in downloading if a.get("local_path") and os.path.isfile(a["local_path"])]
    if ready:
        db.set_status_in_triage([a["id"] for a in ready])

    # Fetch new triage batch
    triage_assets = db.get_in_triage_assets()

    # Spawn next background download
    stream_id = _spawn_download()

    return jsonify({
        "triage_assets": triage_assets,
        "stream_id": stream_id,
        "summary": {
            "kept": kept,
            "archived": archived,
            "deleted": deleted_count,
            "errors": errors,
        },
    })


# ---------------------------------------------------------------------------
# Stats APIs
# ---------------------------------------------------------------------------

@app.route("/api/stats/dashboard")
def api_stats_dashboard():
    return jsonify(db.get_dashboard_stats())


@app.route("/api/stats/pending-breakdown")
def api_stats_pending_breakdown():
    return jsonify(db.get_pending_stats())


@app.route("/api/keep-forever/strip")
def api_keep_forever_strip():
    assets = db.get_keep_forever_assets(limit=20)
    total_bytes = db.get_keep_forever_total_bytes()
    return jsonify({"assets": assets, "total_bytes": total_bytes})


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5001, threaded=True)
