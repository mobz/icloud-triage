## MODIFIED Requirements

### Requirement: Keep-forever assets are copied to copy-to-iphoto folder and kept in iCloud
The system SHALL copy a keep-forever asset's file to `~/Pictures/icloud-triage/copy-to-iphoto/` when the user marks it keep-forever during triage. The asset SHALL remain in iCloud (not deleted). The `keep_forever` flag SHALL be stored in SQLite and persist across sessions.

#### Scenario: Keep-forever decision copies file locally
- **WHEN** the user marks a photo as keep-forever in the triage grid
- **THEN** the file is copied to `~/Pictures/icloud-triage/copy-to-iphoto/` on Next

#### Scenario: Keep-forever asset remains in iCloud
- **WHEN** Next is clicked with a keep-forever photo in the batch
- **THEN** no iCloud delete call is issued for that asset

#### Scenario: Keep-forever flag persists across sessions
- **WHEN** the user marks an asset as keep-forever and later reopens the web UI
- **THEN** the asset is shown in the keep-forever strip in section 2

### Requirement: Keep-forever assets are shown in section 2 strip
The system SHALL display keep-forever assets as a horizontally scrollable thumbnail strip in section 2 of the main triage page.

#### Scenario: Keep-forever strip populated
- **WHEN** assets have `keep_forever = 1` and have been processed (file in copy-to-iphoto/)
- **THEN** their thumbnails appear in the section 2 strip

## REMOVED Requirements

### Requirement: Keep-forever assets are excluded from deletion
**Reason**: Superseded by the new triage model — keep-forever is now a triage decision that skips iCloud deletion. The exclusion logic is the same but is now part of the Next processing step rather than a batch delete filter.
**Migration**: Logic moves from `deleter.py` bulk filter to `POST /api/triage/next` per-asset processing.

### Requirement: Deletion count reflects protected assets
**Reason**: The separate bulk delete flow and its count display are removed. The triage grid shows per-photo decisions inline.
**Migration**: None — deletion count is no longer a UI element.
