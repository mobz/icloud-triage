# Live Photos & Burst Research

## Context

Investigated whether the app correctly handles Live Photos and burst shots.
Ran diagnostic scripts against the live iCloud library (11,281 assets) in April 2026.

**TL;DR:** No Live Photos and no burst photos found in the library at time of research.
The mechanisms for detecting them are understood; downloading Live Photo video companions
is blocked by a pyicloud limitation.

---

## Library composition (sample of last 200 assets)

`assetSubtype` / `assetSubtypeV2` values seen:

| subtype | meaning | count |
|---|---|---|
| `0 / 0` | Standard photo | 145 |
| `None / None` | Old asset, no subtype data | 42 |
| `0 / 3` | Likely HDR or depth effect | 6 |
| `1 / 1` | Panorama (bit 0 set) | 3 |
| `100 / 100` | Streamed video (MOV) | 1 |
| `101 / 101` | Slow-mo / high frame rate (MOV) | 1 |

Apple's `assetSubtype` is a bitmask matching `PHAssetMediaSubtype`:
- Bit 0 (1) = Panorama
- Bit 1 (2) = HDR
- Bit 2 (4) = Screenshot
- **Bit 3 (8) = Live Photo** ← never seen in this library
- Bit 4 (16) = Depth effect

---

## Live Photos

### What a Live Photo actually is on disk (observed via AirDrop with "all photos data")

A single Live Photo AirDrops as a folder containing 5 files:
```
IMG_8388/
  IMG_8388.HEIC       — original still (full res)
  IMG_8388.MOV        — Live Photo video companion (original)
  IMG_E8388.HEIC      — edited still ("E" prefix = edited)
  IMG_E8388.MOV       — edited video companion
  IMG_8388.AAE        — Apple Adjustment Engine file (XML edit instructions)
```

### How iCloud stores them

Live Photos appear as a **single asset** in `photos.all` — not two separate entries.
The video companion is not a separate library item; it lives in the asset's CloudKit record.

### pyicloud versions dict

For normal photos, `photo.versions` contains: `['original', 'medium', 'thumb']`

For Live Photos, you'd expect an `originalVideo` key — but **pyicloud never exposes it**,
even for photos confirmed to be Live Photos. The versions dict only ever shows the three
JPEG/HEIC variants.

### Detection via raw CloudKit record fields

The asset record (accessible via `photo._asset_record['fields']`) contains:

- `assetSubtype` — will have **bit 3 set (value 8 or higher)** for Live Photos
- `vidComplDurValue` / `vidComplDurScale` — video complement duration (non-zero = Live Photo)
- `vidComplVisibilityState` — visibility of the video complement
- `vidComplDispValue` / `vidComplDispScale` — display duration

So detection is possible:
```python
asset_fields = photo._asset_record.get('fields', {})
is_live = bool(asset_fields.get('assetSubtype', {}).get('value', 0) & 8)
# or
vid_dur = asset_fields.get('vidComplDurValue', {}).get('value', 0)
is_live = vid_dur is not None and vid_dur > 0
```

### Downloading the video companion

**Currently blocked.** pyicloud doesn't expose the video resource in `versions`.
The master record contains `resVidSmall*` / `resVidMed*` keys for regular videos,
but for Live Photo companions the resource would be something like `resOriginalVidComplRes`
— which wasn't observed in testing (no Live Photos in the library to test against).

To download it properly would require raw CloudKit API calls beyond what pyicloud provides.
Worth checking pyicloud's GitHub for any newer support before implementing manually.

---

## Burst Photos

### Detection

`burstFlags` in `photo._asset_record['fields']` — non-zero value indicates a burst frame.
`burstId` field would group frames together (not confirmed present; no bursts in library to test).

### How they appear in the library

Each burst frame is a **separate asset** in `photos.all`. They are not grouped.
No burst photos were found in the library at time of testing.

### Implication for the app

Without handling: each burst frame appears as an individual pending asset in the triage queue.
The user would triage them one by one with no indication they're related.

A reasonable improvement: during sync, detect burst frames via `burstFlags` and store a
`burst_id` column in the DB. In the triage UI, group burst frames and let the user pick one
keeper and trash the rest in one action.

---

## Recommended next steps (when Live Photos / bursts are available to test)

1. Take some Live Photos and bursts on the iPhone, let them sync to iCloud
2. Re-run the inspection (or add logging to the sync) to confirm `assetSubtype & 8` fires
3. Check pyicloud for `originalVideo` support in a newer version
4. If pyicloud still doesn't expose it, look at the raw CloudKit `resOriginalVidComplRes`
   field in the master record to construct a download URL directly
5. For bursts: add `burst_id` to the DB schema and group them in the triage grid
