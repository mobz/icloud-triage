## ADDED Requirements

### Requirement: System downloads all media types in original quality
The system SHALL download all asset types available in iCloud Photos — including photos (JPEG, HEIC, RAW), videos (MP4, MOV), panoramas, slow-motion videos, and live photos — in the highest available resolution and original format without transcoding.

#### Scenario: Photo downloaded in original format
- **WHEN** a batch includes a HEIC photo
- **THEN** the file is saved as `.HEIC` at full resolution, not converted

#### Scenario: Video downloaded in original format
- **WHEN** a batch includes a 4K MOV video
- **THEN** the file is saved as the original `.MOV` at full resolution

#### Scenario: All media types included
- **WHEN** a batch is run
- **THEN** photos, videos, panoramas, slow-motion, and live photos are all eligible for download

### Requirement: Each batch downloads the oldest 50 eligible assets
The system SHALL always select exactly the 50 oldest pending assets that are not favorites and not keep-forever, ordered by `taken_at` ascending. This ensures every batch makes progress on assets that will actually be deleted from iCloud.

#### Scenario: Oldest 50 eligible assets selected
- **WHEN** a batch is triggered
- **THEN** the 50 assets with the earliest `taken_at` that have `status = 'pending'`, `is_favorite = 0`, and `keep_forever = 0` are selected

#### Scenario: Protected assets skipped
- **WHEN** the oldest pending assets are favorites or keep-forever
- **THEN** those assets are skipped and the next eligible assets are selected

#### Scenario: Fewer than 50 eligible assets remain
- **WHEN** fewer than 50 eligible pending assets exist
- **THEN** all remaining eligible assets are downloaded without error

### Requirement: Control panel shows oldest eligible pending date
The system SHALL display the capture date of the oldest pending asset that is eligible for download (not a favorite, not keep-forever), so the displayed date reflects real progress.

#### Scenario: Oldest eligible date shown
- **WHEN** the control panel loads and the oldest pending assets are all protected
- **THEN** the displayed "oldest pending" date reflects the oldest non-protected pending asset

### Requirement: Assets are saved in yyyy-mm folder structure
The system SHALL save downloaded assets under `~/Pictures/icloud-archive/<yyyy-mm>/` using the asset's capture date, preserving the original filename.

#### Scenario: File saved to correct folder
- **WHEN** a photo taken in March 2021 is downloaded
- **THEN** it is saved to `~/Pictures/icloud-archive/2021-03/<original-filename>`

#### Scenario: Filename collision resolved
- **WHEN** a file with the same name already exists in the target folder
- **THEN** the new file is saved with a `_2` suffix (e.g., `IMG_1234_2.HEIC`)

### Requirement: Download progress is streamed to the web UI
The system SHALL emit real-time progress updates during a batch download via Server-Sent Events so the web UI can display a progress bar.

#### Scenario: Progress updates emitted
- **WHEN** a batch is running
- **THEN** the web UI receives an update after each asset is downloaded showing current count and total

#### Scenario: Batch completion signalled
- **WHEN** all assets in a batch have been downloaded
- **THEN** a completion event is emitted and the UI transitions to the review view

### Requirement: Asset state is tracked in SQLite
The system SHALL update each asset's record in the `assets` table upon download, recording `local_path`, `downloaded_at`, and setting `status = 'downloaded'`.

#### Scenario: Asset record updated after download
- **WHEN** an asset is successfully downloaded
- **THEN** its SQLite record reflects `status = 'downloaded'`, a valid `local_path`, and a `downloaded_at` timestamp
