## ADDED Requirements

### Requirement: iCloud favorites are automatically protected from deletion
The system SHALL read the `is_favorite` flag from pyicloud for each asset and store it in SQLite. Assets with `is_favorite = 1` SHALL never be included in a deletion batch.

#### Scenario: Favorite displayed with heart icon
- **WHEN** a downloaded asset has `is_favorite = 1`
- **THEN** the web UI displays a filled heart (♥) icon on that asset's thumbnail

#### Scenario: Favorite excluded from deletion
- **WHEN** the user triggers "Delete from iCloud"
- **THEN** any asset with `is_favorite = 1` is excluded from the deletion set regardless of other flags

### Requirement: User can toggle keep-forever on any downloaded asset
The system SHALL allow the user to mark any downloaded asset as keep-forever via the web UI. This flag is stored locally in SQLite and persists across sessions.

#### Scenario: Keep-forever toggled on
- **WHEN** the user clicks the lock icon on an asset showing an open lock (🔓)
- **THEN** the asset's `keep_forever` flag is set to `1` in SQLite and the icon changes to a closed lock (🔒)

#### Scenario: Keep-forever toggled off
- **WHEN** the user clicks the closed lock icon (🔒) on a keep-forever asset
- **THEN** the asset's `keep_forever` flag is set to `0` in SQLite and the icon reverts to open lock (🔓)

#### Scenario: Toggle persists across sessions
- **WHEN** the user marks an asset as keep-forever and later reopens the web UI
- **THEN** the asset still shows the closed lock icon

### Requirement: Keep-forever assets are excluded from deletion
The system SHALL exclude any asset with `keep_forever = 1` from iCloud deletion batches, in addition to favorites.

#### Scenario: Keep-forever asset excluded from deletion
- **WHEN** the user triggers "Delete from iCloud"
- **THEN** assets with `keep_forever = 1` are not deleted from iCloud, even if not favorited

### Requirement: Deletion count reflects protected assets
The system SHALL show the correct count of assets that will actually be deleted (total batch minus favorites and keep-forever) in both the confirm button label and the confirmation dialog.

#### Scenario: Count excludes protected assets
- **WHEN** a batch of 50 contains 3 favorites and 2 keep-forever items
- **THEN** the delete button reads "Delete 45 from iCloud" and the confirm dialog says "You are about to delete 45 photos from iCloud"
