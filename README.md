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

### 4. Download this project

If you have git:

```bash
git clone https://github.com/your-username/icloud-downloader.git
cd icloud-downloader
```

Or download and unzip the project folder, then open Terminal and navigate into it:

```bash
cd ~/Downloads/icloud-downloader
```

### 5. Start the app

```bash
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

### Making decisions

Each photo in the triage grid has two action buttons:

| Button | Action |
|--------|--------|
| **Archive** (box icon, default) | Save locally + delete from iCloud |
| **Lock** (padlock icon) | Save locally + also keep in iCloud |
| **Trash** (bin icon) | Delete from iCloud + save to `for-deletion/` for final review |

Favorites (hearts) are shown for reference — you can still triage them however you like.

### Submitting a batch

Click **Next →** when you're done with a batch. Your decisions are applied immediately:
- Files are moved to their destination folder on disk before any iCloud deletion happens.
- iCloud deletions run in the background so the UI stays responsive.
- The next batch starts downloading automatically.

### Where files go

All files are saved under `~/Pictures/icloud-triage/`:

```
~/Pictures/icloud-triage/
  archive/        ← archived or locked photos (import these into Photos.app)
  for-deletion/   ← trashed (review before permanently deleting)
```

## App state

All app state (credentials, session cookies, photo index) is stored in `~/.icloud-downloader/` with permissions 600.

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
