## Why

Managing iCloud storage is painful — Apple's "Optimize Storage" silently removes local copies, and there's no good tool to systematically download, review, and clean up your iCloud photo library in bulk. This tool solves that for a single local user who wants to archive everything offline while keeping full control over what stays in iCloud.

## What Changes

- New Python CLI tool that authenticates with iCloud via pyicloud and downloads all media in batches (50 photos or 1 month at a time), oldest first
- Full-resolution originals of all media types (photos, videos, panoramas, slow-mo, RAW) saved locally under `yyyy-mm/` folders
- SQLite database tracking every asset's state: downloaded, keep-forever, deleted from iCloud
- iCloud credentials stored in SQLite for session persistence (local use only)
- Dark-themed Flask web app as a local control panel for running batches, reviewing downloaded media, toggling keep-forever, and triggering iCloud deletion
- Confirm dialog before any deletion ("You are about to delete N photos from iCloud")
- Two protection mechanisms: iCloud favorites (never deleted) and a local keep-forever list (toggle per photo)

## Capabilities

### New Capabilities

- `icloud-auth`: Authenticate with iCloud via pyicloud, handle 2FA, persist session and credentials in SQLite
- `media-download`: Fetch all media types in batches from iCloud (oldest first), save originals to `yyyy-mm/` folders, track state in SQLite
- `keep-forever`: Per-photo keep-forever toggle stored locally; combined with iCloud favorites to determine deletion eligibility
- `icloud-delete`: Trigger deletion of a reviewed batch from iCloud with confirmation, skipping favorites and keep-forever items
- `web-app`: Dark-themed Flask control panel — run batches, view photo grid with favorite/keep-forever indicators, trigger deletion

### Modified Capabilities

## Impact

- **New dependencies**: `pyicloud`, `flask`, `pillow` (thumbnails), `sqlite3` (stdlib)
- **New files**: `app.py` (Flask), `downloader.py` (pyicloud logic), `db.py` (SQLite), `static/`, `templates/`
- **Local storage**: `~/Pictures/icloud-archive/yyyy-mm/` for downloaded media
- **No external services**: runs entirely on localhost, no cloud backend
