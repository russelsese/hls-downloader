#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import json
import time
import shutil
import socket
from typing import Optional


def prompt_if_missing(value: Optional[str], prompt: str) -> str:
    if value:
        return value
    val = input(prompt).strip()
    if not val:
        print("Error: value cannot be empty.", file=sys.stderr)
        sys.exit(1)
    return val


def ensure_mp4_extension(filename: str) -> str:
    if not filename.lower().endswith(".mp4"):
        filename += ".mp4"
    return filename


def get_duration(url: str) -> Optional[float]:
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            raw = data.get("format", {}).get("duration", "")
            return float(raw) if raw else None
    except Exception:
        pass
    return None


def fmt_duration(seconds: Optional[float]) -> str:
    if seconds is None or seconds < 0:
        return "--:--"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def fmt_size(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    if b < 1024 ** 2:
        return f"{b / 1024:.1f} KB"
    if b < 1024 ** 3:
        return f"{b / 1024 ** 2:.1f} MB"
    return f"{b / 1024 ** 3:.2f} GB"


def parse_speed(speed_str: str) -> Optional[float]:
    """Parse ffmpeg speed string like '2.5x' into a float multiplier."""
    try:
        return float(speed_str.rstrip("x"))
    except (ValueError, AttributeError):
        return None


def check_tor() -> None:
    try:
        with socket.create_connection(("127.0.0.1", 9050), timeout=5):
            pass
    except OSError:
        print("Error: Tor daemon is not running. Start it with: brew services start tor", file=sys.stderr)
        sys.exit(1)

    if not shutil.which("torsocks"):
        print("Error: torsocks not found. Install with: brew install torsocks", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        ["curl", "--socks5", "127.0.0.1:9050", "-s", "--max-time", "10",
         "https://check.torproject.org/api/ip"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("Error: Could not reach Tor network. Is Tor fully bootstrapped?", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Error: Unexpected response from Tor check endpoint.", file=sys.stderr)
        sys.exit(1)

    if not data.get("IsTor"):
        print("Error: Connected but traffic is NOT routing through Tor.", file=sys.stderr)
        sys.exit(1)

    print(f"Tor active — exit node IP: {data['IP']}")


def render_progress(
    current: float,
    total: Optional[float],
    speed_str: str,
    size: int,
    elapsed: float,
) -> None:
    BAR_W = 28
    speed = parse_speed(speed_str)

    if total and total > 0:
        pct = min(current / total, 1.0)
        filled = int(BAR_W * pct)
        bar = "█" * filled + "░" * (BAR_W - filled)
        pct_label = f"{pct * 100:5.1f}%"
        remaining = (total - current) / speed if speed else None
        eta = f"ETA {fmt_duration(remaining)}"
    else:
        spinner = "▌▀▐▄"[int(elapsed) % 4]
        bar = f"{spinner}" + "░" * (BAR_W - 1)
        pct_label = "  ?  "
        eta = "ETA --:--"

    time_label = fmt_duration(current)
    if total:
        time_label += f"/{fmt_duration(total)}"

    speed_label = f"{speed_str}" if speed_str and speed_str != "N/A" else ""
    size_label = fmt_size(size) if size else ""

    parts = list(filter(None, [size_label, speed_label, eta]))
    line = f"\r[{bar}] {pct_label}  {time_label}  {', '.join(parts)}"

    cols = shutil.get_terminal_size().columns
    print(line[:cols], end="", flush=True)


def download_hls(url: str, output: str, use_tor: bool = False) -> None:
    output = ensure_mp4_extension(output)

    if os.path.exists(output):
        answer = input(f"'{output}' already exists. Overwrite? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    print("Fetching stream info…")
    total_duration = get_duration(url)
    print(f"  Duration : {fmt_duration(total_duration)}")
    print(f"  Output   : {output}\n")

    ffmpeg_cmd = ["torsocks", "ffmpeg"] if use_tor else ["ffmpeg"]
    cmd = [
        *ffmpeg_cmd, "-y",
        "-i", url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-progress", "pipe:1",
        "-nostats",
        output,
    ]

    start = time.time()
    current_sec = 0.0
    total_size = 0
    speed = ""

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )

    for line in process.stdout:
        key, _, val = line.strip().partition("=")
        if key == "out_time_ms":
            try:
                current_sec = int(val) / 1_000_000
            except ValueError:
                pass
        elif key == "total_size":
            try:
                total_size = int(val)
            except ValueError:
                pass
        elif key == "speed":
            speed = val.strip()
        elif key == "progress":
            render_progress(current_sec, total_duration, speed, total_size, time.time() - start)
            if val.strip() == "end":
                break

    process.wait()
    print()  # move past progress line

    elapsed = time.time() - start

    if process.returncode != 0:
        print("Download failed.", file=sys.stderr)
        sys.exit(process.returncode)

    file_size = os.path.getsize(output) if os.path.exists(output) else 0
    print(f"  Saved    : {output}")
    print(f"  File size: {fmt_size(file_size)}")
    print(f"  Took     : {fmt_duration(elapsed)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download an HLS stream and save it as MP4 with live progress."
    )
    parser.add_argument("url", nargs="?", help="HLS playlist URL (.m3u8)")
    parser.add_argument("output", nargs="?", help="Output filename (e.g. video.mp4)")
    parser.add_argument("--tor", action="store_true", help="Route download through Tor (requires tor + torsocks)")
    args = parser.parse_args()

    if args.tor:
        check_tor()

    url = prompt_if_missing(args.url, "HLS URL (.m3u8): ")
    output = prompt_if_missing(args.output, "Output filename: ")

    download_hls(url, output, use_tor=args.tor)


if __name__ == "__main__":
    main()
