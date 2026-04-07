## MODIFIED Requirements

### Requirement: Deletion fires immediately per decision when Next is clicked
The system SHALL delete assets from iCloud immediately when the user clicks Next, as part of processing triage decisions. There is no separate deferred deletion step. Assets marked trash or left untagged (defaulting to copy-to-iphoto) are deleted from iCloud at this point. Assets marked keep-forever are NOT deleted from iCloud.

#### Scenario: Trash decision triggers immediate deletion
- **WHEN** the user clicks Next and a photo was marked trash
- **THEN** that asset is deleted from iCloud during the Next processing step

#### Scenario: Untagged decision triggers immediate deletion
- **WHEN** the user clicks Next and a photo was not tagged (defaulting to copy-to-iphoto)
- **THEN** that asset is deleted from iCloud during the Next processing step

#### Scenario: Keep-forever decision skips deletion
- **WHEN** the user clicks Next and a photo was marked keep-forever (lock)
- **THEN** that asset is NOT deleted from iCloud

## ADDED Requirements

### Requirement: System verifies local file exists and is non-zero before deleting from iCloud
The system SHALL confirm that the local destination file (in `copy-to-iphoto/` or `for-deletion/`) exists on disk and has a size greater than zero bytes before issuing any iCloud delete call. If the file is missing or zero bytes, the iCloud deletion SHALL be skipped for that asset and the failure logged.

#### Scenario: File present and non-zero — deletion proceeds
- **WHEN** Next is processing a trash or untagged decision
- **THEN** the system checks the destination file exists and `os.path.getsize() > 0` before calling the iCloud delete API

#### Scenario: File missing — deletion skipped
- **WHEN** the destination file does not exist at the expected path
- **THEN** the iCloud delete call is NOT issued for that asset, and the error is recorded in the Next response summary

#### Scenario: File is zero bytes — deletion skipped
- **WHEN** the destination file exists but has size zero
- **THEN** the iCloud delete call is NOT issued for that asset, and the error is recorded in the Next response summary

## REMOVED Requirements

### Requirement: User must confirm before deletion executes
**Reason**: The Next button replaces the separate bulk-delete flow. Deletion is now per-decision and part of the triage flow. The triage interaction itself (choosing lock/trash/neither before clicking Next) is the confirmation step.
**Migration**: None — the new model is triage decisions → Next → immediate deletion.

### Requirement: Deletion progress is streamed to the web UI
**Reason**: Deletion now happens synchronously as part of the Next request for the small batch of 10. No separate progress stream is needed.
**Migration**: The Next button response includes a summary of deletions performed.

### Requirement: Deletion report shown after completion
**Reason**: Replaced by the inline Next response — decisions and outcomes are reflected in the triage grid transition and section 5 count update.
**Migration**: None.

### Requirement: Deletion is always manually triggered
**Reason**: Replaced by the more specific requirement that deletion fires on Next as part of triage decisions. Manual intent is preserved — the user must click Next.
**Migration**: None.
