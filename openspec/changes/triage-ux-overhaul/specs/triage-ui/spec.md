## ADDED Requirements

### Requirement: Main page has five vertical sections
The system SHALL render a single unified page with five sections stacked vertically: (1) dashboard, (2) keep-forever strip, (3) triage grid, (4) download progress bar, (5) pending summary.

#### Scenario: All five sections render on load
- **WHEN** the user opens the main page
- **THEN** all five sections are visible in order from top to bottom

### Requirement: Section 1 — Dashboard shows asset stats and re-sync control
The dashboard SHALL display: total pending asset count, estimated total size of pending assets (from `size_bytes` sum), and a Re-sync button that triggers a full index sync from iCloud.

#### Scenario: Stats shown on load
- **WHEN** the main page loads
- **THEN** section 1 shows pending asset count and estimated pending size from the SQLite DB

#### Scenario: Re-sync updates stats
- **WHEN** the user clicks Re-sync and the sync completes
- **THEN** the pending count and size update to reflect the latest iCloud index

### Requirement: Section 2 — Keep-forever strip shows curated phone collection
The keep-forever strip SHALL show a horizontally scrollable row of the most recent keep-forever asset thumbnails (up to 20) and the total byte count of all keep-forever assets.

#### Scenario: Keep-forever thumbnails shown
- **WHEN** any assets have `keep_forever = 1`
- **THEN** their thumbnails appear in section 2 in reverse chronological order (newest first)

#### Scenario: Byte count shown
- **WHEN** section 2 renders
- **THEN** the total size of all keep-forever assets is shown (e.g., "1.4 GB")

#### Scenario: Empty state when no keep-forever assets
- **WHEN** no assets have `keep_forever = 1`
- **THEN** section 2 shows a placeholder (e.g., "No keep-forever photos yet")

### Requirement: Section 3 — Triage grid shows current batch with per-photo decision controls
The triage grid SHALL display a 2-row grid of 5 photo thumbnails each (10 total). Each thumbnail SHALL have a lock icon and a trash icon overlay. Clicking lock toggles keep-forever for that photo. Clicking trash marks it for deletion. Untagged photos default to copy-to-iphoto on Next.

#### Scenario: Grid renders 10 thumbnails in 2 rows
- **WHEN** a triage batch of 10 is loaded
- **THEN** 10 thumbnails appear in a 2×5 grid (5 per row)

#### Scenario: Lock icon toggles keep-forever state
- **WHEN** the user clicks the lock icon on a photo
- **THEN** the icon changes from open (outline) to closed (filled, accent colour) and the photo is marked keep-forever

#### Scenario: Trash icon marks for deletion
- **WHEN** the user clicks the trash icon on a photo
- **THEN** the icon becomes active (accent/danger colour) and the photo is marked for-deletion

#### Scenario: Untagged photos default to copy-to-iphoto
- **WHEN** the user clicks Next without tagging a photo
- **THEN** that photo is treated as copy-to-iphoto (copied locally, deleted from iCloud)

#### Scenario: Lock and trash are mutually exclusive
- **WHEN** the user clicks trash on a photo already marked keep-forever
- **THEN** the keep-forever mark is cleared and the photo is marked for-deletion instead

### Requirement: Next button processes current batch and advances pipeline
The Next button SHALL: (1) send all triage decisions to the server, (2) trigger immediate iCloud deletion for trash and untagged photos, (3) promote the pre-downloaded batch to triage, (4) start a background download for the following batch.

#### Scenario: Decisions processed on Next
- **WHEN** the user clicks Next
- **THEN** each photo in the triage grid is moved to its destination folder and iCloud deletion fires for non-keep-forever photos

#### Scenario: New batch appears after Next
- **WHEN** the user clicks Next
- **THEN** the triage grid updates to show the next batch of photos

### Requirement: Section 4 — Download progress bar shows background batch download
Section 4 SHALL be hidden when no background download is active. When a download is running, it SHALL show a progress bar and count (e.g., "Downloading 6/10").

#### Scenario: Progress bar hidden when idle
- **WHEN** no background batch is downloading
- **THEN** section 4 is not visible

#### Scenario: Progress bar visible during download
- **WHEN** a background batch download is in progress
- **THEN** section 4 shows a progress bar updating in real time

### Requirement: Section 5 — Pending summary shows what remains to be processed
Section 5 SHALL display: total count of pending assets, total estimated size, and a breakdown of counts by file extension (e.g., HEIC: 2,841 · MOV: 891 · JPG: 312).

#### Scenario: Pending stats shown
- **WHEN** the main page loads
- **THEN** section 5 shows total pending count, total estimated size, and per-type breakdown

#### Scenario: Stats update after Next
- **WHEN** the user completes a triage batch
- **THEN** section 5 counts decrease to reflect processed assets
