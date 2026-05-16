# HLS Downloader

Download HTTP Live Streaming (HLS) videos and save them as MP4 files, with live progress, duration, and ETA display.

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) (includes `ffprobe`)

```bash
# macOS
brew install ffmpeg
```

## Usage

```bash
python3 hls_download.py [url] [output]
```

Both arguments are optional — the script will prompt for any that are missing.

### Examples

```bash
# Pass both arguments directly
python3 hls_download.py "https://example.com/stream.m3u8" my_video.mp4

# Omit the .mp4 extension — it's added automatically
python3 hls_download.py "https://example.com/stream.m3u8" my_video

# Interactive mode — prompts for both
python3 hls_download.py

# Pass only the URL — prompts for filename
python3 hls_download.py "https://example.com/stream.m3u8"
```

### Output

```
Fetching stream info…
  Duration : 01:02:15
  Output   : my_video.mp4

[████████████░░░░░░░░░░░░░░░░] 43.2%  00:26/01:02:15  18.3 MB, 2.1x, ETA 00:32

  Saved    : my_video.mp4
  File size: 412.7 MB
  Took     : 00:28
```

## Features

| Feature | Details |
|---|---|
| Progress bar | Live bar that redraws in-place as the download runs |
| Duration | Fetched upfront via `ffprobe` before download starts |
| ETA | Calculated from remaining video time and ffmpeg's reported speed |
| Speed | Displays ffmpeg's real-time multiplier (e.g. `2.5x`) |
| File size | Running byte count during download, final size on completion |
| Overwrite guard | Prompts before overwriting an existing file |
| Auto extension | Appends `.mp4` if the output filename doesn't include it |

## Notes

- Uses `ffmpeg -c copy` (stream copy) — no re-encoding, so it's fast and lossless.
- When total duration cannot be determined (some live streams), the progress bar shows an animated spinner instead of a percentage.
