## ADDED Requirements

### Requirement: User can configure iCloud credentials
The system SHALL provide a setup screen where the user enters their Apple ID and password. Credentials SHALL be stored in SQLite after successful authentication.

#### Scenario: First-time credential entry
- **WHEN** the user visits the app with no credentials stored
- **THEN** the setup screen is shown before any other view

#### Scenario: Credentials saved after auth
- **WHEN** the user submits valid credentials and completes 2FA
- **THEN** the Apple ID and password are stored in the `credentials` table

### Requirement: System handles Apple two-factor authentication
The system SHALL detect when pyicloud requires a 2FA code and prompt the user to enter the 6-digit code sent to their trusted device.

#### Scenario: 2FA prompt shown
- **WHEN** pyicloud signals that 2FA verification is required
- **THEN** the web UI displays a 2FA code entry field without requiring page reload

#### Scenario: Valid 2FA code accepted
- **WHEN** the user submits a correct 6-digit 2FA code
- **THEN** the session is verified and the session data is persisted to SQLite

#### Scenario: Invalid 2FA code rejected
- **WHEN** the user submits an incorrect 2FA code
- **THEN** an error message is shown and the user can try again

### Requirement: Session is persisted and reused
The system SHALL store pyicloud session data in SQLite and reuse it on subsequent runs to avoid repeated 2FA prompts.

#### Scenario: Existing session reused
- **WHEN** the downloader starts and valid session data exists in SQLite
- **THEN** pyicloud is initialised with the stored session and no 2FA is required

#### Scenario: Expired session triggers re-auth
- **WHEN** pyicloud raises an authentication error during a batch operation
- **THEN** the web UI shows a "Session expired — re-authenticate" prompt

### Requirement: User can re-authenticate
The system SHALL allow the user to trigger a fresh authentication from the web UI settings page.

#### Scenario: Re-authenticate clears old session
- **WHEN** the user clicks "Re-authenticate" in settings
- **THEN** the stored session data is cleared and the setup flow is restarted
