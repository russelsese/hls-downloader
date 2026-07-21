# HLS Downloader

Download HTTP Live Streaming (HLS) videos and save them as MP4 files, with live progress, duration, and ETA display.

Two scripts are available:

| Script | Description |
|---|---|
| `hls_download.py` | Standard downloader — direct connection |
| `tor_hls_download.py` | Tor variant — routes traffic through the Tor network |

## Requirements

- Python 3.10+
- ffmpeg 4.0+ with `ffprobe` (bundled with ffmpeg)

No third-party Python packages are needed — see [requirements.txt](requirements.txt).

### Installing ffmpeg

#### macOS

Using [Homebrew](https://brew.sh):

```bash
brew install ffmpeg
```

Verify:

```bash
ffmpeg -version
```

#### Linux (Ubuntu / Debian)

```bash
sudo apt update && sudo apt install -y ffmpeg
```

#### Linux (Fedora / RHEL)

```bash
sudo dnf install ffmpeg
```

> If `ffmpeg` is not found on Fedora, enable the RPM Fusion repo first:
> ```bash
> sudo dnf install https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
> sudo dnf install ffmpeg
> ```

#### Linux (Arch)

```bash
sudo pacman -S ffmpeg
```

#### Windows

**Option 1 — winget (Windows 11 / Windows 10 with App Installer):**

```powershell
winget install --id Gyan.FFmpeg
```

**Option 2 — Chocolatey:**

```powershell
choco install ffmpeg
```

**Option 3 — manual:**

1. Download a build from <https://www.gyan.dev/ffmpeg/builds/> (choose `ffmpeg-release-essentials.zip`)
2. Extract to a folder, e.g. `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system `PATH`:
   - Search **Edit the system environment variables** → **Environment Variables**
   - Under **System variables**, select `Path` → **Edit** → **New** → paste `C:\ffmpeg\bin`
4. Open a new terminal and verify:

```powershell
ffmpeg -version
```

## Usage

### Standard (`hls_download.py`)

```bash
python3 hls_download.py [url] [output]
```

Both positional arguments are optional — the script will prompt for any that are missing.

#### Examples

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

### Tor variant (`tor_hls_download.py`)

Routes all traffic through the Tor network. Tor is always active — there is no opt-in flag. Requires `tor` and `torsocks` (macOS).

#### Installing Tor (macOS only)

```bash
brew install tor torsocks
brew services start tor   # starts the Tor daemon (runs in background)
```

Verify Tor is running:

```bash
brew services list | grep tor
```

#### Usage

```bash
python3 tor_hls_download.py [url] [output]
```

The script automatically verifies the Tor connection before downloading and prints the exit node IP.

#### Examples

```bash
# Pass both arguments directly
python3 tor_hls_download.py "https://example.com/stream.m3u8" my_video.mp4

# Interactive mode
python3 tor_hls_download.py
```

## Output

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
