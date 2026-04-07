## Context

A single-user local tool to systematically drain iCloud Photos storage by downloading full-resolution originals, reviewing them via a web UI, and selectively deleting from iCloud. The tool must handle Apple's 2FA authentication flow and pyicloud's session management. All state lives in SQLite on the local machine. No networking beyond iCloud API calls.

## Goals / Non-Goals

**Goals:**
- Authenticate with iCloud once, persist session to avoid repeated 2FA
- Download the oldest 50 eligible assets per batch (excludes favorites and keep-forever)
- Track every asset's lifecycle in SQLite
- Web UI as a local control panel — review, mark, trigger deletion
- Protect favorites (from iCloud) and keep-forever items (local list) from deletion
- Confirm before any destructive iCloud operation

**Non-Goals:**
- Multi-user support
- Cloud-hosted deployment
- Two-way sync (changes made to local files are not pushed back)
- Album structure mirroring beyond `yyyy-mm/` date folders
- Uploading or modifying photos in iCloud

## Decisions

### 1. SQLite as single source of truth

All state — credentials, session tokens, asset metadata, keep-forever list, download status, deletion status — lives in one SQLite file (`~/.icloud-downloader/db.sqlite`).

**Why not separate files/config?** A single DB means atomic updates, easy querying for the web UI, and one thing to back up. The keep-forever list, download log, and credentials are all naturally relational.

**Schema sketch:**
```
assets
  id TEXT PRIMARY KEY        -- iCloud asset id
  filename TEXT
  media_type TEXT            -- photo, video, panorama, etc.
  taken_at DATETIME
  size_bytes INTEGER
  local_path TEXT
  status TEXT                -- pending | downloaded | deleted
  is_favorite INTEGER        -- from iCloud
  keep_forever INTEGER       -- local flag
  downloaded_at DATETIME
  deleted_at DATETIME

credentials
  id INTEGER PRIMARY KEY
  apple_id TEXT
  password TEXT              -- plaintext, local use only
  session_data TEXT          -- JSON blob from pyicloud

batches
  id INTEGER PRIMARY KEY
  started_at DATETIME
  completed_at DATETIME
  asset_count INTEGER
  deleted_count INTEGER
```

### 2. Downloader as standalone subprocess

The Flask app spawns `downloader.py` as a subprocess and streams its stdout back to the browser via Server-Sent Events (SSE). This keeps the CLI independently usable and makes progress streaming natural.

**Why not import directly?** pyicloud's download operations are blocking and long-running. Running them in a subprocess avoids blocking Flask's event loop and keeps the web process responsive. SSE from subprocess stdout is a proven local pattern.

### 3. Fixed batch of 50, oldest eligible first

Each batch always downloads the 50 oldest assets that are `status = 'pending'`, `is_favorite = 0`, and `keep_forever = 0`, ordered by `taken_at ASC`. No batch mode selector — one button, one behaviour. Favorites and keep-forever items are excluded so that progress is never blocked by protected photos accumulating at the old end of the timeline.

### 4. Deletion is always manual and confirmed

The downloader never auto-deletes. Deletion is a separate explicit action in the web UI:
1. User reviews the batch
2. User clicks "Delete from iCloud"
3. Modal confirms: "You are about to delete N photos from iCloud. Your local copies are safe."
4. User confirms → `deleter.py` subprocess runs

Assets with `is_favorite = 1` or `keep_forever = 1` are excluded from the deletion set regardless.

### 5. File organization: `yyyy-mm/` flat

```
~/Pictures/icloud-archive/
  2019-01/
    IMG_1234.MOV
    IMG_1235.HEIC
  2019-02/
    ...
```

Original filenames preserved. If collision, append `_2`, `_3` etc. No album mirroring — albums in iCloud are mutable metadata, date is stable.

### 6. Dark-themed plain HTML/JS frontend

No build step. Flask serves templates directly. CSS uses CSS custom properties for the dark theme. JavaScript uses `fetch()` and `EventSource` for SSE. No framework — this is a single-user local tool, not a product.

### 7. Credentials stored in SQLite plaintext

Acceptable for a local personal tool. The database lives in `~/.icloud-downloader/` with permissions `600`. A future improvement could use the OS keychain, but that adds complexity without meaningful benefit for local-only use.

## Risks / Trade-offs

**pyicloud session expiry** → Mitigation: detect auth errors in the downloader, surface a "Re-authenticate" prompt in the web UI. Session cookies typically last weeks.

**2FA required on every new session** → Mitigation: persist full session data in SQLite; reuse until expired. Most users won't see 2FA more than once a month.

**Large video files (4K, slow-mo)** → Mitigation: show file sizes before batch runs; no automatic disk space check in v1 (out of scope).

**pyicloud rate limiting / API instability** → Mitigation: add retry with backoff in downloader; pyicloud is a reverse-engineered API and can break with Apple updates.

**Duplicate filenames across months** → Mitigation: collision detection on write (`_2`, `_3` suffix).

**iCloud deletion is irreversible** → Mitigation: confirm dialog, local copy verified to exist before delete call is made.

## Open Questions

- Should deleted assets be removable from the local grid view (hide vs. show with strikethrough)?
- Thumbnail generation: serve originals scaled via `<img>` CSS, or pre-generate thumbs? (Originals could be 50MB RAW files — probably need thumbs.)
