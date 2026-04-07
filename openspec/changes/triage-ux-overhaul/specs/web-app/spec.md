## MODIFIED Requirements

### Requirement: Main page is a unified triage page with five sections
The system SHALL render a single main page (`/`) containing all five triage sections. There is no separate review page. The index and review flows are merged into one unified interface.

#### Scenario: Single page renders all content
- **WHEN** the user navigates to `/`
- **THEN** all five sections (dashboard, keep-forever strip, triage grid, download progress, pending summary) are shown on one page

### Requirement: Photo thumbnails are served for the triage grid
The system SHALL serve JPEG thumbnails for all triage assets via the existing `/thumb/<asset_id>` route. Thumbnails are generated on download and cached. The triage grid uses thumbnails, not full-resolution images.

#### Scenario: Thumbnails served in triage grid
- **WHEN** the triage grid renders
- **THEN** each photo card uses the `/thumb/<asset_id>` route

## REMOVED Requirements

### Requirement: Control panel triggers a batch download with a single button
**Reason**: The separate "Download Next 50" control panel is replaced by the unified triage page. Downloading is now handled by the JIT pipeline automatically.
**Migration**: The triage page's Next button drives the pipeline; no explicit download trigger button needed.

### Requirement: Photo grid displays downloaded batch with status indicators
**Reason**: Replaced by the triage grid (section 3) with new per-photo lock/trash decision controls.
**Migration**: The triage grid in section 3 serves this function.

### Requirement: Delete button triggers deletion flow with confirmation
**Reason**: Bulk delete with confirmation modal is replaced by per-decision immediate deletion on Next.
**Migration**: Deletion is now triggered as part of the Next button flow in the triage grid.

### Requirement: Images are served directly from local filesystem
**Reason**: Replaced by thumbnail serving. Full-resolution images are available via `/photo/<asset_id>` but the triage grid uses thumbnails.
**Migration**: The `/photo/<asset_id>` route remains for direct access; the grid now uses `/thumb/<asset_id>`.
