## 1. Database — Status Values and Queries

- [x] 1.1 Update `db.py`: change `get_eligible_batch_asset_ids()` LIMIT from 50 to 10
- [x] 1.2 Add `get_in_triage_assets()` query — returns all assets with `status = 'in_triage'` ordered by `taken_at ASC`
- [x] 1.3 Add `get_downloading_next_assets()` query — returns all assets with `status = 'downloading_next'`
- [x] 1.4 Add `set_status_in_triage(asset_ids)` — bulk update status to `in_triage`
- [x] 1.5 Add `set_status_downloading_next(asset_ids)` — bulk update status to `downloading_next`
- [x] 1.6 Add `set_status_keep_forever(asset_id, local_path)` — update status to `keep_forever`, set local_path
- [x] 1.7 Add `set_status_to_iphoto(asset_id, local_path)` — update status to `to_iphoto`, set local_path, set deleted_at
- [x] 1.8 Add `set_status_for_deletion(asset_id, local_path)` — update status to `for_deletion`, set local_path, set deleted_at
- [x] 1.9 Add `get_keep_forever_assets(limit=20)` — returns most recent keep_forever assets for section 2 strip
- [x] 1.10 Add `get_keep_forever_total_bytes()` — returns SUM(size_bytes) for keep_forever assets
- [x] 1.11 Add `get_pending_stats()` — returns count, sum(size_bytes), and per-extension breakdown for pending assets
- [x] 1.12 Update `init_db()` migration: set any existing `status='downloaded'` rows to `status='to_iphoto'`

## 2. Folder Structure

- [x] 2.1 Update `ARCHIVE_DIR` constant in `downloader.py` to `~/Pictures/icloud-triage/triage/`
- [x] 2.2 Define `COPY_TO_IPHOTO_DIR = ~/Pictures/icloud-triage/copy-to-iphoto/` and `FOR_DELETION_DIR = ~/Pictures/icloud-triage/for-deletion/` constants (in `downloader.py` or a shared `config.py`)
- [x] 2.3 Update `_resolve_path()` in `downloader.py` to use flat triage folder (no date subfolders)
- [x] 2.4 Ensure all three folders are created on startup (`os.makedirs(..., exist_ok=True)`)

## 3. Downloader — Pipeline Integration

- [x] 3.1 Update `download_batch()` to set `status = 'downloading_next'` on selected assets before downloading
- [x] 3.2 After download completes per-asset, leave status as `downloading_next` (promotion to `in_triage` happens on Next)
- [x] 3.3 Update `complete_batch()` call to reflect new status flow (or remove if batch table no longer needed for pipeline)
- [x] 3.4 On app startup in `app.py`, check for any `in_triage` assets and ensure they are surfaced to the triage grid (recovery logic)

## 4. Triage Processing — `POST /api/triage/next` Endpoint

- [x] 4.1 Create `POST /api/triage/next` route in `app.py` — accepts JSON body `{decisions: {asset_id: "lock"|"trash"|null}}`
- [x] 4.2 For each decision: resolve file path and move file from `triage/` to appropriate destination folder
- [x] 4.3 For `"lock"` decisions: copy file to `copy-to-iphoto/`, call `set_status_keep_forever()`, do NOT delete from iCloud
- [x] 4.4 For `"trash"` decisions: copy file to `for-deletion/`, call `set_status_for_deletion()`, delete from iCloud via pyicloud
- [x] 4.5 For `null` (untagged) decisions: copy file to `copy-to-iphoto/`, call `set_status_to_iphoto()`, delete from iCloud via pyicloud
- [x] 4.5a Before issuing any iCloud delete call, verify destination file exists and `os.path.getsize() > 0`; skip deletion and record error in summary if check fails
- [x] 4.6 Promote `downloading_next` assets to `in_triage` (bulk status update)
- [x] 4.7 Spawn background download subprocess for the next `pending` batch, store in `_streams`
- [x] 4.8 Return JSON: `{triage_assets: [...], stream_id: "...", summary: {kept: N, to_iphoto: N, deleted: N}}`

## 5. Flask Routes — Cleanup and New Endpoints

- [x] 5.1 Remove `/run-batch`, `/delete-batch`, `/review`, `/api/batch/current`, `/api/deletable-count` routes
- [x] 5.2 Add `GET /api/triage/current` — returns current `in_triage` assets (for page load)
- [x] 5.3 Add `GET /api/stats/dashboard` — returns pending count, pending size, keep-forever count, keep-forever size
- [x] 5.4 Add `GET /api/stats/pending-breakdown` — returns per-extension counts and total for section 5
- [x] 5.5 Add `GET /api/keep-forever/strip` — returns last 20 keep-forever assets with thumbnail URLs
- [x] 5.6 Update `GET /` to render `triage.html` (replacing `index.html`)
- [x] 5.7 Keep `/sync-index` route and SSE stream (re-sync button still uses this)
- [x] 5.8 Keep `/thumb/<path:asset_id>` and `/photo/<path:asset_id>` routes unchanged

## 6. Templates — New Triage Page

- [x] 6.1 Create `templates/triage.html` extending `base.html` with five-section layout
- [x] 6.2 Section 1: dashboard with pending count, estimated pending size, Re-sync button and SSE progress
- [x] 6.3 Section 2: keep-forever strip — scrollable row of thumbnails + total byte count, empty state message
- [x] 6.4 Section 3: triage grid — 2×5 grid of photo cards, each with lock icon and trash icon overlays, Next button
- [x] 6.5 Section 4: download progress bar (hidden when idle, visible during background download via SSE)
- [x] 6.6 Section 5: pending summary — total count, total size, per-type badge breakdown
- [x] 6.7 JS: on page load, fetch `/api/triage/current` and render grid; if empty, trigger first batch download
- [x] 6.8 JS: lock/trash toggle logic — mutually exclusive, visual state change on click, store decisions in memory
- [x] 6.9 JS: Next button — POST decisions to `/api/triage/next`, update grid with returned assets, start SSE for background download progress
- [x] 6.10 JS: SSE handler for background download progress (section 4 progress bar)
- [x] 6.11 JS: re-sync button — POST to `/sync-index`, show SSE progress in section 1, refresh stats on complete
- [x] 6.12 Delete `templates/index.html` and `templates/review.html`

## 7. Styles

- [x] 7.1 Add five-section layout styles to `style.css` (vertical stack, section separators)
- [x] 7.2 Add keep-forever strip styles — horizontal scroll row, thumbnail size, byte count label
- [x] 7.3 Update triage grid — slightly larger thumbnails than current review grid, 5-per-row layout
- [x] 7.4 Add per-photo decision overlay styles — lock icon (top-left), trash icon (top-right), active/inactive states
- [x] 7.5 Ensure lock and trash icons are visually distinct: inactive = muted border colour, active = accent/danger colour

## 8. Deleter — Simplify for Per-Decision Use

- [x] 8.1 Add `delete_single_asset(asset_id)` function in `deleter.py` (or inline in app.py) for immediate per-asset iCloud deletion
- [x] 8.2 Remove or deprecate `delete_batch()` bulk deletion flow in `deleter.py` (no longer called by app)
