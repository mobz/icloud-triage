#!/usr/bin/env python3
"""
deleter.py — iCloud asset deletion helpers.

delete_single_asset(asset_id) is called directly (not as subprocess) for
per-decision immediate deletion in the triage pipeline.
"""
import os
import sys

import db
from auth import get_icloud_api, AuthRequired, TwoFactorRequired


def delete_single_asset(asset_id):
    """
    Delete a single asset from iCloud. Returns (success: bool, message: str).
    Caller is responsible for verifying local file exists before calling this.
    """
    try:
        api = get_icloud_api()
    except (AuthRequired, TwoFactorRequired) as e:
        return False, f"Auth error: {e}"

    # Scan library with early exit to find the photo object
    for photo in api.photos.all:
        if photo.id == asset_id:
            try:
                photo.delete()
                return True, "deleted"
            except Exception as e:
                return False, str(e)

    # Not found in library — treat as already deleted
    return True, "not found in iCloud (already deleted)"


# --- Legacy bulk deletion (no longer called by app.py) ---

def _progress(msg):
    print(msg, flush=True)


def delete_batch(batch_id, dry_run=False):
    """Deprecated: bulk batch deletion. Kept for reference."""
    assets = db.get_batch_assets(batch_id)
    eligible = [
        a for a in assets
        if a["status"] in ("downloaded", "to_iphoto", "archive", "for_deletion")
        and a["is_favorite"] == 0
        and a["keep_forever"] == 0
    ]

    skipped = len(assets) - len(eligible)
    _progress(f"DELETE_START: {len(eligible)} to delete, {skipped} protected (batch {batch_id})")

    if not eligible:
        _progress("SUMMARY: deleted=0 skipped=0 errors=0")
        return

    try:
        api = get_icloud_api()
    except (AuthRequired, TwoFactorRequired) as e:
        _progress(f"AUTH_ERROR: {e}")
        sys.exit(1)

    photo_map = {p.id: p for p in api.photos.all}

    deleted = 0
    errors = 0

    for i, asset in enumerate(eligible, 1):
        asset_id = asset["id"]
        local_path = asset.get("local_path")

        if not local_path or not os.path.isfile(local_path):
            _progress(f"ERROR: local file missing for {asset['filename']}, skipping delete")
            errors += 1
            continue

        photo = photo_map.get(asset_id)
        if not photo:
            _progress(f"WARN: {asset['filename']} not found in iCloud library, marking deleted anyway")
            if not dry_run:
                db.mark_deleted(asset_id)
            deleted += 1
            _progress(f"PROGRESS: {i}/{len(eligible)} {asset['filename']}")
            continue

        try:
            if dry_run:
                _progress(f"DRY_RUN: would delete {asset['filename']} from iCloud")
            else:
                photo.delete()
                db.mark_deleted(asset_id)
            deleted += 1
            _progress(f"PROGRESS: {i}/{len(eligible)} {asset['filename']}")
        except Exception as e:
            _progress(f"ERROR: failed to delete {asset['filename']}: {e}")
            errors += 1

    _progress(f"SUMMARY: deleted={deleted} skipped={skipped} errors={errors}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-id", type=int, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    db.init_db()
    delete_batch(args.batch_id, dry_run=args.dry_run)
