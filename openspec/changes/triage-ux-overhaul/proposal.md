## Why

The current tool has a batch-oriented workflow (sync → download 50 → review grid → bulk delete) that doesn't match how the tool is actually used: opening it periodically to free iCloud space by routing photos to one of three destinations. The existing UI has no sense of storage urgency, no unified view of progress, and no just-in-time pipeline — the user waits for a full batch to download before doing anything.

## What Changes

- **BREAKING**: Replace date-based archive folder (`~/Pictures/icloud-archive/yyyy-mm/`) with three purpose-based folders: `triage/`, `copy-to-iphoto/`, `for-deletion/`
- **BREAKING**: Replace multi-page app (index + review) with a single unified page with five vertical sections
- **BREAKING**: Asset `status` field gains new values: `in_triage`, `keep_forever`, `to_iphoto`, `for_deletion` (replaces `downloaded`)
- Add per-photo lock/trash toggle icons in the triage grid; untagged photos default to `to_iphoto` on Next
- Add JIT pipeline: Next button processes current batch, promotes pre-downloaded batch, starts downloading following batch in background
- iCloud deletion fires immediately on Next (not at end of a separate review step)
- Remove separate `/review` and batch delete flow; replace with inline triage decisions
- Add keep-forever strip (section 2): single scrollable row of last N keep-forever thumbnails + total byte count
- Add still-to-process summary (section 5): count by file type, total asset count, estimated byte total

## Capabilities

### New Capabilities

- `triage-pipeline`: JIT download pipeline — pre-fetches next batch while user triages current; Next button processes decisions, promotes batch, starts next download
- `triage-ui`: Single-page unified interface with five sections: dashboard, keep-forever strip, triage grid, download progress, pending summary

### Modified Capabilities

- `media-download`: Download destination changes from date-based folders to flat `triage/` staging; batch size reduced to 10; download feeds triage pipeline rather than review grid
- `icloud-delete`: Deletion now fires immediately per-decision (on Next) rather than as a separate bulk operation at end of review
- `keep-forever`: Keep-forever now also copies file to `copy-to-iphoto/` locally (previously had no local copy); keep-forever strip added to UI
- `web-app`: Single-page layout replaces multi-page; `/review` route removed; `/` becomes the unified triage page

## Impact

- `downloader.py`: new batch size (10), destination folder changes, pipeline state management
- `deleter.py`: per-asset immediate deletion replaces bulk batch deletion
- `db.py`: new status values, new queries for pipeline state (which batch is in_triage, which is downloading_next)
- `app.py`: routes restructured; `/review`, `/run-batch`, `/delete-batch` replaced with triage pipeline endpoints
- `templates/`: `review.html` and `index.html` replaced with single `triage.html`
- `static/style.css`: new five-section layout styles
- Folder paths change — existing downloaded files in `icloud-archive/` are not migrated automatically
