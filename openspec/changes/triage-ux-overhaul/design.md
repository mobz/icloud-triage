## Context

The app currently separates concerns across multiple pages and a batch-oriented pipeline: index (stats + trigger), review (grid + delete). Downloads happen in a bulk subprocess, deletion is a separate bulk step. There is no concept of "where is this photo going locally" — everything lands in `~/Pictures/icloud-archive/yyyy-mm/`.

The new model is a single-page triage loop. The user makes three-way decisions (keep in iCloud / save locally / delete) and the system immediately acts on iCloud deletion. Local files are routed to one of two staging folders. A JIT pipeline keeps the next batch pre-downloaded so the user never waits.

## Goals / Non-Goals

**Goals:**
- Single unified page replacing index + review
- Three-way per-photo decision: lock (keep in iCloud + copy locally), trash (for-deletion + delete from iCloud), neither (copy-to-iphoto + delete from iCloud)
- iCloud deletion fires immediately when Next is clicked, not deferred
- JIT pipeline: always one batch pre-downloading in background
- Five-section layout: dashboard, keep-forever strip, triage grid, download progress, pending summary
- Batch size of 10 (fits 2 rows of 5 in grid)
- Flat folder structure (no date subfolders)

**Non-Goals:**
- Automatic import into Photos.app (manual for now)
- Migration of existing files in `icloud-archive/`
- iCloud storage quota display (pyicloud doesn't expose this reliably; show DB-derived stats instead)
- Multi-account support

## Decisions

### Decision 1: New asset status values

Current `status` values (`pending`, `downloaded`, `deleted`) don't capture pipeline state.

New values:
- `pending` — in iCloud, not yet touched
- `in_triage` — downloaded to `triage/`, currently shown to user
- `downloading_next` — being downloaded as background pre-fetch
- `keep_forever` — user locked it; file in `copy-to-iphoto/`, kept in iCloud
- `to_iphoto` — user defaulted or chose save; file in `copy-to-iphoto/`, deleted from iCloud
- `for_deletion` — user trashed it; file in `for-deletion/`, deleted from iCloud

Rationale: Status is the single source of truth for pipeline position. Avoids needing a separate `batch` concept for the triage pipeline (though the `batches` table can remain for history).

### Decision 2: Per-photo decision stored client-side until Next

Lock/trash toggles on each photo card update in-browser state only. When Next is clicked, a single POST `/api/triage/next` sends the full decision map `{asset_id: "lock"|"trash"|null}`. The server processes all decisions atomically, then returns the next batch.

Alternative considered: fire an API call on each toggle. Rejected — creates race conditions if user clicks quickly, and requires more server round-trips.

### Decision 3: Next button is a single synchronous endpoint

`POST /api/triage/next` does in one request:
1. Receives decisions for current `in_triage` batch
2. Moves files to appropriate folders
3. Fires iCloud deletions for `trash` and `null` decisions
4. Promotes `downloading_next` batch to `in_triage`
5. Returns new triage batch (thumbnails already exist)
6. Triggers background download of next `pending` batch (subprocess)

Returns JSON with the new triage assets. The background download progress is polled separately via SSE on `/stream/<stream_id>`.

Rationale: Atomic from the UI's perspective — one click, one response, new photos appear. Background download is fire-and-forget.

### Decision 4: Folder structure

```
~/Pictures/icloud-triage/
  triage/           # working area, cleared as items are processed
  copy-to-iphoto/   # both keep-forever and to-iphoto land here
  for-deletion/     # condemned, user reviews before trash
```

`keep_forever` and `to_iphoto` assets both go to `copy-to-iphoto/` — the distinction is only in the DB and in whether iCloud deletion fires. Locally they are identical.

### Decision 5: Dashboard stats from DB, not iCloud API

iCloud storage quota is not reliably accessible via pyicloud. The dashboard shows DB-derived stats: total pending count, estimated bytes (sum of `size_bytes`), breakdown by file extension. A re-sync button updates the index from iCloud.

### Decision 6: Keep-forever strip queries DB

Section 2 queries `SELECT * FROM assets WHERE keep_forever=1 ORDER BY downloaded_at DESC LIMIT 20`. Thumbnails already exist. Byte count is `SUM(size_bytes)`. No new data needed.

## Risks / Trade-offs

- **iCloud deletion is immediate and hard to undo** → Only fires on Next (not on toggle), giving user a moment to reconsider. No undo after Next.
- **`triage/` folder accumulates if app crashes mid-Next** → On startup, any `in_triage` assets with files still in `triage/` should be re-promoted to the triage grid rather than lost. Handle in init.
- **Background download subprocess outlives its stream** → Use existing `_streams` dict pattern; progress bar polls the stream, disappears on `done` event.
- **10 photos per batch may feel slow for large libraries** → Batch size is a single constant, easy to tune. Start at 10.
- **Existing `icloud-archive/` files are orphaned** → Acceptable. This is a local tool, user can manually move files. Document in dev-reset script.

## Migration Plan

1. Run `db.py` migration: add new status values (SQLite TEXT column, no schema change needed — just update application logic)
2. Set all existing `status='downloaded'` rows to `status='to_iphoto'` (already processed)
3. Update `ARCHIVE_DIR` constant in `downloader.py` to new folder paths
4. New routes replace old ones — no redirect needed (local tool, no external consumers)
5. Old templates (`index.html`, `review.html`) deleted; new `triage.html` added

Rollback: restore from git. No DB schema changes that can't be reverted.

## Open Questions

- Should the triage grid show `taken_at` date on each thumbnail? Useful for context when triaging.
- Should re-sync in the dashboard be a full sync or incremental (only new assets)? pyicloud doesn't have an incremental API, so full sync is the only option — just show a spinner.
