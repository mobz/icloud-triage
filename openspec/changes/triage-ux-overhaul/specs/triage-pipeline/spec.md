## ADDED Requirements

### Requirement: System maintains a JIT download pipeline with two buffer slots
The system SHALL maintain two pipeline slots beyond the currently visible triage batch: one slot for the batch actively in triage (`in_triage`), one for the pre-downloaded next batch (`downloading_next`). When the user advances, the `downloading_next` batch promotes to `in_triage` and a new background download fills the `downloading_next` slot.

#### Scenario: Pipeline advances on Next
- **WHEN** the user clicks Next
- **THEN** the `in_triage` batch is processed, the `downloading_next` batch becomes `in_triage`, and a new download starts for the following batch

#### Scenario: Next batch instantly available
- **WHEN** the user clicks Next and the `downloading_next` batch is fully downloaded
- **THEN** the new triage grid renders immediately with no waiting

#### Scenario: Next batch not yet ready
- **WHEN** the user clicks Next and background download is still in progress
- **THEN** the triage area shows a loading state until the batch is ready

### Requirement: Background batch download starts automatically after Next
The system SHALL automatically start downloading the next `pending` batch (10 assets) in the background after the user clicks Next, without requiring any additional user action.

#### Scenario: Background download starts after Next
- **WHEN** the user clicks Next and triage decisions are processed
- **THEN** a background subprocess begins downloading the following pending batch

#### Scenario: Progress bar reflects background download
- **WHEN** a background batch download is in progress
- **THEN** section 4 (download progress bar) is visible and updates in real time via SSE

#### Scenario: Progress bar hides when complete
- **WHEN** the background batch download completes
- **THEN** the progress bar in section 4 disappears

### Requirement: Batch size is 10 assets
The system SHALL select exactly 10 pending eligible assets per batch (not 50), ordered by `taken_at` ascending, excluding `is_favorite = 1` and `keep_forever = 1`.

#### Scenario: 10 oldest eligible assets selected
- **WHEN** a batch is built
- **THEN** exactly 10 assets with the earliest `taken_at` that are `pending`, not favorite, not keep-forever are selected

### Requirement: On startup, in-flight triage state is recovered
The system SHALL detect any assets with `status = 'in_triage'` on startup and restore them to the triage grid rather than losing them.

#### Scenario: Crash recovery
- **WHEN** the app starts and assets have `status = 'in_triage'`
- **THEN** those assets are shown in the triage grid as if the session had not been interrupted
