#!/usr/bin/env python3
"""
downloader.py — iCloud photo downloader (run as subprocess by app.py or standalone CLI).

Usage:
  python downloader.py --sync          # sync asset index from iCloud
  python downloader.py --download      # download next batch of 10 into triage/
  python downloader.py --download --dry-run
"""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import time

import pillow_heif
pillow_heif.register_heif_opener()
from PIL import Image, ImageFile, ImageOps
ImageFile.LOAD_TRUNCATED_IMAGES = True

import db
from auth import get_icloud_api, AuthRequired, TwoFactorRequired
from config import TRIAGE_DIR, BATCH_SIZE

THUMB_DIR = os.path.expanduser("~/.icloud-downloader/thumbs")
THUMB_SIZE = (400, 400)


def _progress(msg):
    print(msg, flush=True)


def sync_asset_index():
    _progress("Connecting to iCloud...")
    try:
        api = get_icloud_api()
    except (AuthRequired, TwoFactorRequired) as e:
        _progress(f"AUTH_ERROR: {e}")
        sys.exit(1)

    library = api.photos.all
    total = len(library)
    _progress(f"SYNC_TOTAL: {total}")

    type_counts = {}
    for i, photo in enumerate(library, 1):
        try:
            asset_id = photo.id
            filename = photo.filename
            media_type = getattr(photo, "media_type", "photo") or "photo"
            taken_at = str(photo.asset_date) if photo.asset_date else None
            size_bytes = getattr(photo, "size", None)
            is_favorite = 1 if getattr(photo, "is_favorite", False) else 0
            db.upsert_asset(asset_id, filename, media_type, taken_at, size_bytes, is_favorite)
            ext = os.path.splitext(filename)[1].upper().lstrip(".") or "OTHER"
            type_counts[ext] = type_counts.get(ext, 0) + 1
        except Exception as e:
            _progress(f"WARN: skipped asset {i}: {e}")

        if i % 100 == 0:
            counts_str = "  ".join(f"{k}:{v}" for k, v in sorted(type_counts.items()))
            _progress(f"SYNC_PROGRESS: {i}/{total}  {counts_str}")

    counts_str = "  ".join(f"{k}:{v}" for k, v in sorted(type_counts.items()))
    _progress(f"SYNC_DONE: {total}  {counts_str}")


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


def _download_with_retry(photo, dest_path, dry_run=False, retries=3):
    if dry_run:
        _progress(f"DRY_RUN: would download {dest_path}")
        return
    delay = 2
    for attempt in range(1, retries + 1):
        try:
            url = photo.download_url("original")
            if not url:
                raise Exception("No download URL for 'original' version")
            response = photo._service.session.get(url, stream=True)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
            return
        except Exception as e:
            if attempt == retries:
                raise
            _progress(f"RETRY {attempt}/{retries} for {photo.filename}: {e}")
            time.sleep(delay)
            delay *= 2


def _thumb_path(asset_id):
    safe = hashlib.md5(asset_id.encode()).hexdigest()
    return os.path.join(THUMB_DIR, f"{safe}.jpg")


VIDEO_EXTENSIONS = {".mov", ".mp4", ".m4v", ".avi", ".mkv", ".3gp"}


def _generate_thumb(asset_id, local_path):
    os.makedirs(THUMB_DIR, exist_ok=True)
    thumb_path = _thumb_path(asset_id)
    ext = os.path.splitext(local_path)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        _generate_thumb_video(asset_id, local_path, thumb_path)
    else:
        _generate_thumb_image(local_path, thumb_path)


def _generate_thumb_image(local_path, thumb_path):
    try:
        img = Image.open(local_path)
        img = ImageOps.exif_transpose(img)
        img.thumbnail(THUMB_SIZE)
        img = img.convert("RGB")
        img.save(thumb_path, "JPEG", quality=80)
    except Exception as e:
        _progress(f"WARN: could not generate image thumbnail for {local_path}: {e}")


def _generate_thumb_video(asset_id, local_path, thumb_path):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", "0",
                "-i", local_path,
                "-vframes", "1",
                "-vf", f"scale={THUMB_SIZE[0]}:{THUMB_SIZE[1]}:force_original_aspect_ratio=decrease",
                tmp_path,
            ],
            capture_output=True,
            timeout=30,
        )
        if result.returncode == 0 and os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 0:
            os.replace(tmp_path, thumb_path)
            tmp_path = None
        else:
            _progress(f"WARN: ffmpeg failed for {local_path}: {result.stderr.decode(errors='replace')[-200:]}")
    except FileNotFoundError:
        _progress("WARN: ffmpeg not found — install with 'brew install ffmpeg' for video thumbnails")
    except Exception as e:
        _progress(f"WARN: could not generate video thumbnail for {local_path}: {e}")
    finally:
        if tmp_path and os.path.isfile(tmp_path):
            os.unlink(tmp_path)


def download_batch(dry_run=False):
    asset_ids = db.get_eligible_batch_asset_ids()
    if not asset_ids:
        _progress("BATCH_EMPTY: no eligible assets")
        return

    # Mark as downloading_next before we start
    if not dry_run:
        db.set_status_downloading_next(asset_ids)

    os.makedirs(TRIAGE_DIR, exist_ok=True)

    _progress(f"BATCH_START: {len(asset_ids)} assets")

    try:
        api = get_icloud_api()
    except (AuthRequired, TwoFactorRequired) as e:
        _progress(f"AUTH_ERROR: {e}")
        sys.exit(1)

    # Scan library for just the assets we need
    _progress(f"SCAN_START: looking for {len(asset_ids)} assets in library...")
    remaining = set(asset_ids)
    photo_map = {}
    for j, p in enumerate(api.photos.all, 1):
        if p.id in remaining:
            photo_map[p.id] = p
            remaining.discard(p.id)
        if j % 500 == 0:
            _progress(f"SCAN_PROGRESS: scanned {j}, found {len(photo_map)}/{len(asset_ids)}")
        if not remaining:
            break
    _progress(f"SCAN_DONE: found {len(photo_map)}/{len(asset_ids)}")

    downloaded = 0
    for i, asset_id in enumerate(asset_ids, 1):
        asset = db.get_asset(asset_id)
        photo = photo_map.get(asset_id)
        if not photo:
            _progress(f"WARN: asset {asset_id} not found in library, skipping")
            continue

        dest_path = _resolve_path(TRIAGE_DIR, asset["filename"])

        try:
            _download_with_retry(photo, dest_path, dry_run=dry_run)
            if not dry_run:
                db.update_local_path(asset_id, dest_path)
                _generate_thumb(asset_id, dest_path)
            downloaded += 1
            _progress(f"PROGRESS: {i}/{len(asset_ids)} {asset['filename']}")
        except Exception as e:
            _progress(f"ERROR: failed to download {asset['filename']}: {e}")

    _progress(f"BATCH_DONE: {downloaded}/{len(asset_ids)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync", action="store_true")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db.init_db()

    if args.sync:
        sync_asset_index()
    elif args.download:
        download_batch(dry_run=args.dry_run)
    else:
        parser.print_help()
