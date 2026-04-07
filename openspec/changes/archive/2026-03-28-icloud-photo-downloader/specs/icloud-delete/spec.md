## ADDED Requirements

### Requirement: Deletion is always manually triggered
The system SHALL never automatically delete assets from iCloud. Deletion MUST be initiated by an explicit user action in the web UI.

#### Scenario: No auto-delete after download
- **WHEN** a batch download completes
- **THEN** no assets are deleted from iCloud automatically

### Requirement: User must confirm before deletion executes
The system SHALL show a confirmation modal before executing any iCloud deletion, stating the exact number of assets that will be deleted.

#### Scenario: Confirm dialog shown
- **WHEN** the user clicks "Delete from iCloud"
- **THEN** a modal appears with the message "You are about to delete N photos from iCloud. Your local copies are safe." and Confirm / Cancel buttons

#### Scenario: Cancel aborts deletion
- **WHEN** the user clicks Cancel in the confirmation modal
- **THEN** no assets are deleted and the UI returns to the review view unchanged

#### Scenario: Confirm triggers deletion
- **WHEN** the user clicks Confirm in the confirmation modal
- **THEN** the deletion process starts for the eligible assets in the current batch

### Requirement: System verifies local copy exists before deleting from iCloud
The system SHALL check that the local file exists at the stored `local_path` before issuing the iCloud delete call for each asset.

#### Scenario: Local file missing — skip deletion
- **WHEN** an asset's `local_path` does not exist on disk at deletion time
- **THEN** that asset is skipped, not deleted from iCloud, and flagged as an error in the deletion report

#### Scenario: Local file present — deletion proceeds
- **WHEN** an asset's local file is confirmed present on disk
- **THEN** the iCloud delete call is issued for that asset

### Requirement: Deletion progress is streamed to the web UI
The system SHALL emit real-time progress events during deletion via SSE so the user can see which assets are being deleted.

#### Scenario: Progress shown during deletion
- **WHEN** deletion is running
- **THEN** the web UI displays a progress indicator showing how many assets have been deleted out of the total

### Requirement: Asset state is updated after deletion
The system SHALL update each successfully deleted asset's record in SQLite, setting `status = 'deleted'` and recording `deleted_at`.

#### Scenario: SQLite updated after deletion
- **WHEN** an asset is successfully deleted from iCloud
- **THEN** its record shows `status = 'deleted'` and a valid `deleted_at` timestamp

### Requirement: Deletion report shown after completion
The system SHALL display a summary after deletion completes showing how many assets were deleted, how many were skipped (protected), and any errors.

#### Scenario: Summary shown
- **WHEN** a deletion batch completes
- **THEN** the UI shows "Deleted N • Kept M (favorites/locked) • Errors E"
