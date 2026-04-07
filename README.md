# iCloud Downloader

A local web app that lets you systematically work through your iCloud photo library — downloading batches, triaging each photo, and deleting originals from iCloud to free up storage while keeping everything safe on disk.

## Requirements

- macOS
- Python 3.9+
- ffmpeg (optional — needed for video thumbnails)

## Setup

### 1. Install Homebrew (if you don't have it)

Homebrew is a package manager for macOS. Open Terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python

```bash
brew install python
```

### 3. Install ffmpeg (optional, for video thumbnails)

```bash
brew install ffmpeg
```

### 4. Start the app

```bash
cd icloud-triage # where you saved it (maybe Downloads) or require unzipping
./start.sh
```

Then open **http://localhost:5001** in your browser.

The script creates a virtual environment, installs dependencies if needed, and starts the app. Just run `./start.sh` every time.

## First run

1. Enter your Apple ID and password on the setup screen.
   - If you have two-factor authentication enabled (recommended), use an [app-specific password](https://support.apple.com/en-us/102654) instead of your regular password.
2. If prompted, enter the 6-digit 2FA code sent to your trusted device.
3. Once logged in, click **Re-sync** to fetch your full iCloud photo library index. This may take several minutes for large libraries.

## Triage workflow

The app downloads photos in batches of 10 and presents them for review one batch at a time.

It works well to open the `~/Pictures/icloud-triage/triage` folder. This way you can preview files at full res while performing the traige operation.

| Button | Action |
|--------|--------|
| **Archive** | (the defatult) - Removes the file from icloud and saves it locally into the `archive` directory |
| **Lock** | Leaves the file in icloud instead of removing it - this way it will be on your photo forever |
| **Delete** | Removes the file from icloud and saves locally into the `for-deletion` directory |

Your favorites (hearts) are shown for reference — you can still triage them however you like, but they are locked by default.

### Submitting a batch

Click **Next →** when you're done with a batch. Your decisions are applied immediately:
- Files are moved to their destination folder on disk before any iCloud deletion happens.
- iCloud deletions run in the background so the UI stays responsive.
- The next batch starts downloading automatically.

### Where files go

All files are saved under `~/Pictures/icloud-triage/`:

```
~/Pictures/icloud-triage/
  triage/         ← photos that are in the currect and next batch to be triaged
  archive/        ← archived and locked photos (import these into Photos.app)
  for-deletion/   ← trashed (review before permanently deleting if you like)
```

## App state

All app state (credentials, session cookies, photo index) is stored in `~/Pictures/icloud-triage/app-data/` alongside your photos.

## CLI usage

You can also drive the downloader directly from Terminal (make sure the venv is active first: `source .venv/bin/activate`):

```bash
# Sync asset index from iCloud
python3 downloader.py --sync

# Download next batch of 10 (dry run — no files written)
python3 downloader.py --download --dry-run

# Download next batch of 10
python3 downloader.py --download
```
