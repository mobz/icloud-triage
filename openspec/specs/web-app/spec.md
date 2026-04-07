## ADDED Requirements

### Requirement: Web app uses a dark theme
The system SHALL render all UI with a dark colour scheme using CSS custom properties. The background SHALL be dark (near-black), text SHALL be light, and accent colours SHALL be clearly visible against the dark background.

#### Scenario: Dark theme applied globally
- **WHEN** the user opens the web app in any browser
- **THEN** all pages render with a dark background and light text

### Requirement: Control panel triggers a batch download with a single button
The system SHALL provide a main control panel with a single "Download Next 50" button. There is no batch mode selector or month picker.

#### Scenario: Download triggered
- **WHEN** the user clicks "Download Next 50"
- **THEN** the downloader subprocess starts and a progress bar appears

#### Scenario: Oldest eligible date shown
- **WHEN** the control panel loads
- **THEN** it displays the capture date of the oldest eligible pending asset (not a favorite, not keep-forever) and the total count of eligible pending assets

### Requirement: Photo grid displays downloaded batch with status indicators
The system SHALL display a grid of images for the most recently downloaded batch, served directly from the local filesystem, with visual indicators for favorites and keep-forever status.

#### Scenario: Favorite shown with heart icon
- **WHEN** a downloaded asset has `is_favorite = 1`
- **THEN** a filled heart icon (♥) is overlaid on its thumbnail

#### Scenario: Keep-forever shown with closed lock icon
- **WHEN** a downloaded asset has `keep_forever = 1`
- **THEN** a closed lock icon (🔒) is shown below its thumbnail

#### Scenario: Normal asset shows open lock icon
- **WHEN** a downloaded asset has `keep_forever = 0` and `is_favorite = 0`
- **THEN** an open lock icon (🔓) is shown below its thumbnail, clickable to toggle

### Requirement: Images are served directly from local filesystem
The system SHALL serve local image files directly via a Flask route without any resizing or pre-processing. CSS SHALL constrain display size in the grid.

#### Scenario: Image served from local path
- **WHEN** the photo grid loads and requests an image
- **THEN** Flask serves the file from its `local_path` on disk with no transformation

### Requirement: Delete button triggers deletion flow with confirmation
The system SHALL display a "Delete N from iCloud" button on the review view that shows the count of deletable assets and triggers the confirmation modal on click.

#### Scenario: Delete button shows correct count
- **WHEN** the review view renders a batch of 50 with 5 protected assets
- **THEN** the button reads "Delete 45 from iCloud"

#### Scenario: Confirmation modal shown on click
- **WHEN** the user clicks the delete button
- **THEN** a modal overlay appears with the confirmation message and Confirm / Cancel buttons

### Requirement: Setup screen shown when credentials are absent
The system SHALL redirect to a setup/authentication screen when no credentials are stored in SQLite.

#### Scenario: No credentials — setup shown
- **WHEN** the user visits any page and no credentials exist in SQLite
- **THEN** they are redirected to the setup screen

#### Scenario: Authenticated — main UI shown
- **WHEN** valid credentials and a live session exist
- **THEN** the control panel is shown directly

### Requirement: Settings page allows re-authentication and credential update
The system SHALL provide a settings page where the user can update their Apple ID, password, or trigger re-authentication.

#### Scenario: Settings accessible from nav
- **WHEN** the user clicks the settings link in the navigation
- **THEN** the settings page is shown with current Apple ID displayed and a re-authenticate button
