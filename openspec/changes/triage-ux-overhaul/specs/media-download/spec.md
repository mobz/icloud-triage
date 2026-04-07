## MODIFIED Requirements

### Requirement: Each batch downloads the oldest 10 eligible assets
The system SHALL always select exactly the 10 oldest pending assets that are not favorites and not keep-forever, ordered by `taken_at` ascending. This ensures every batch makes incremental progress on assets that will be removed from iCloud.

#### Scenario: Oldest 10 eligible assets selected
- **WHEN** a batch is triggered
- **THEN** the 10 assets with the earliest `taken_at` that have `status = 'pending'`, `is_favorite = 0`, and `keep_forever = 0` are selected

#### Scenario: Protected assets skipped
- **WHEN** the oldest pending assets are favorites or keep-forever
- **THEN** those assets are skipped and the next eligible assets are selected

#### Scenario: Fewer than 10 eligible assets remain
- **WHEN** fewer than 10 eligible pending assets exist
- **THEN** all remaining eligible assets are downloaded without error

### Requirement: Assets are downloaded to the flat triage folder
The system SHALL save downloaded assets to `~/Pictures/icloud-triage/triage/` with no date-based subdirectory structure. The original filename is preserved.

#### Scenario: File saved to triage folder
- **WHEN** any asset is downloaded
- **THEN** it is saved to `~/Pictures/icloud-triage/triage/<original-filename>`

#### Scenario: Filename collision resolved
- **WHEN** a file with the same name already exists in the triage folder
- **THEN** the new file is saved with a `_2` suffix (e.g., `IMG_1234_2.HEIC`)

## REMOVED Requirements

### Requirement: Assets are saved in yyyy-mm folder structure
**Reason**: Replaced by purpose-based flat folder structure. The tool is now a triage router, not a date-based archive.
**Migration**: Existing files in `~/Pictures/icloud-archive/` are not automatically migrated. Users should manually move or leave existing files in place.

### Requirement: Control panel shows oldest eligible pending date
**Reason**: The control panel is replaced by the unified triage page (section 1 dashboard). Stats are shown in the dashboard and section 5 summary instead.
**Migration**: Pending stats are shown in section 1 (dashboard) and section 5 (pending summary) of the new triage page.
