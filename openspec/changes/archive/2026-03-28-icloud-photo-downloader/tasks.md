## 1. Project Setup

- [x] 1.1 Create project directory structure (`app.py`, `downloader.py`, `deleter.py`, `db.py`, `templates/`, `static/`)
- [x] 1.2 Create `requirements.txt` with `pyicloud`, `flask`
- [x] 1.3 Create `db.py` with SQLite initialisation — create `assets`, `credentials`, and `batches` tables
- [x] 1.4 Create `~/.icloud-downloader/` directory and set permissions to 700

## 2. Authentication

- [x] 2.1 Implement `db.py` functions: `get_credentials()`, `save_credentials()`, `get_session()`, `save_session()`, `clear_session()`
- [x] 2.2 Implement `auth.py` helper: `get_icloud_api()` — loads credentials from SQLite, restores pyicloud session, raises `AuthRequired` if expired
- [x] 2.3 Implement Flask setup route (`GET/POST /setup`) — renders credential entry form, calls pyicloud, handles 2FA prompt, saves session on success
- [x] 2.4 Implement Flask 2FA route (`POST /setup/verify`) — accepts 6-digit code, validates with pyicloud, saves session data to SQLite
- [x] 2.5 Implement `before_request` guard — redirect to `/setup` if no credentials in SQLite
- [x] 2.6 Implement settings route (`GET /settings`) with re-authenticate button and current Apple ID display
- [x] 2.7 Implement `POST /settings/re-auth` — clears session from SQLite and redirects to `/setup`

## 3. Asset Index

- [x] 3.1 Implement `downloader.py` function `sync_asset_index()` — fetches full asset list from pyicloud Photos library, upserts into `assets` table with `taken_at`, `filename`, `media_type`, `is_favorite`, `size_bytes`, status defaulting to `pending`
- [x] 3.2 Implement Flask route `POST /sync-index` that spawns `sync_asset_index()` and returns asset counts (total, pending, oldest pending date)
- [x] 3.3 Implement Flask route `GET /api/stats` returning JSON with eligible pending count and oldest eligible pending date — excluding `is_favorite = 1` and `keep_forever = 1`

## 4. Batch Download

- [x] 4.1 Implement `downloader.py` function `build_batch()` — queries SQLite for the 50 oldest assets with `status = 'pending'`, `is_favorite = 0`, `keep_forever = 0`, ordered by `taken_at ASC`
- [x] 4.2 Implement `downloader.py` function `download_batch(asset_ids)` — downloads each asset at original quality, resolves filename collisions, saves to `~/Pictures/icloud-archive/yyyy-mm/`, updates SQLite record with `local_path`, `downloaded_at`, `status='downloaded'`; prints SSE-formatted progress lines to stdout
- [x] 4.3 Implement Flask route `POST /run-batch` — no parameters, spawns `downloader.py` as subprocess, returns stream ID
- [x] 4.4 Implement Flask SSE route `GET /stream/<stream_id>` — streams subprocess stdout as `text/event-stream` to browser
- [x] 4.5 Handle batch completion event — emit `event: done` with final count when subprocess exits

## 5. Photo Review Grid

- [x] 5.1 Implement Flask route `GET /photo/<asset_id>` — serves the local file directly from its `local_path` using `send_file`
- [x] 5.2 Implement Flask route `GET /review` — queries SQLite for most recent batch of downloaded assets, renders grid template
- [x] 5.3 Implement Flask route `GET /api/batch/current` — returns JSON list of assets in the current batch with `id`, `filename`, `media_type`, `is_favorite`, `keep_forever`, `taken_at`
- [x] 5.4 Implement Flask route `POST /api/keep-forever/<asset_id>` — toggles `keep_forever` flag in SQLite, returns new value
- [x] 5.5 Implement Flask route `GET /api/deletable-count` — returns count of current batch assets eligible for deletion (not favorite, not keep_forever)

## 6. iCloud Deletion

- [x] 6.1 Implement `deleter.py` function `delete_batch(asset_ids)` — for each asset: verify local file exists, call pyicloud delete, update SQLite `status='deleted'` and `deleted_at`; print SSE-formatted progress to stdout; skip and log error if local file missing
- [x] 6.2 Implement Flask route `POST /delete-batch` — accepts `{batch_id}` JSON, builds eligible asset list (exclude favorites and keep_forever), spawns `deleter.py` subprocess, returns stream ID
- [x] 6.3 Reuse SSE streaming route from task 4.4 for deletion progress
- [x] 6.4 Emit deletion summary event (`event: summary`) with deleted count, skipped count, error count when subprocess exits

## 7. Web UI — Templates & Styles

- [x] 7.1 Create `templates/base.html` — dark theme layout with CSS custom properties (`--bg`, `--surface`, `--text`, `--accent`), navigation links (Home, Review, Settings)
- [x] 7.2 Create `static/style.css` — dark theme CSS: `--bg: #0f0f0f`, `--surface: #1a1a1a`, `--text: #e8e8e8`, `--accent: #4a9eff`; grid layout, icon styles, button styles, progress bar, modal overlay
- [x] 7.3 Create `templates/setup.html` — credential entry form and 2FA code entry form (shown/hidden via JS)
- [x] 7.4 Create `templates/index.html` — control panel: stats (oldest eligible pending date, eligible pending count), "Download Next 50" button, progress bar (hidden until run)
- [x] 7.5 Create `templates/review.html` — photo grid with images served via `/photo/<asset_id>`, heart overlay for favorites, lock icon toggle for keep-forever, delete button with count, confirmation modal
- [x] 7.6 Create `templates/settings.html` — shows current Apple ID, re-authenticate button
- [x] 7.7 Create `static/app.js` — SSE connection for progress bar, keep-forever toggle fetch calls, delete button click → modal → confirm → SSE deletion stream, modal open/close logic

## 8. Polish & Safety

- [x] 8.1 Add `--dry-run` flag to `downloader.py` — logs what would be downloaded without saving files or updating SQLite
- [x] 8.2 Add `--dry-run` flag to `deleter.py` — logs what would be deleted without calling pyicloud
- [x] 8.3 Add retry with exponential backoff (3 attempts) to pyicloud download calls in `downloader.py`
- [x] 8.4 Add a `README.md` with setup instructions: install deps, first run, how to use the web UI
