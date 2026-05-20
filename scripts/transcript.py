from __future__ import annotations
import re
import subprocess
from pathlib import Path
from typing import List

from scripts.models import CapabilityMap, VideoContext, VideoInput
from scripts.utils import append_log


def vtt_to_markdown(vtt_content: str) -> str:
    lines = vtt_content.splitlines()
    entries: List[tuple[str, str]] = []
    timestamp = ""
    text_lines: List[str] = []

    for line in lines:
        line = line.strip()
        if line == "WEBVTT" or line.startswith("NOTE") or not line:
            if text_lines and timestamp:
                entries.append((timestamp, " ".join(text_lines)))
                text_lines = []
                timestamp = ""
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}", line) and "-->" in line:
            if text_lines and timestamp:
                entries.append((timestamp, " ".join(text_lines)))
                text_lines = []
            timestamp = line.split("-->")[0].strip()
            continue
        if re.match(r"^\d+$", line):
            continue
        text_lines.append(line)

    if text_lines and timestamp:
        entries.append((timestamp, " ".join(text_lines)))

    # Deduplicate consecutive identical text
    deduped: List[tuple[str, str]] = []
    for ts, text in entries:
        if not deduped or deduped[-1][1] != text:
            deduped.append((ts, text))

    return "\n".join(f"[{ts}] {text}" for ts, text in deduped)


def _find_existing_vtt(captions_dir: Path) -> Path | None:
    for pattern in ["*.en.vtt", "*.en-US.vtt", "*.vtt"]:
        matches = list(captions_dir.glob(pattern))
        if matches:
            return matches[0]
    return None


def _run_yt_dlp_captions(url: str, captions_dir: Path, log_path: Path) -> bool:
    cmd = [
        "yt-dlp",
        "--write-auto-sub",
        "--write-sub",
        "--sub-lang", "en",
        "--skip-download",
        "--no-warnings",
        "-o", str(captions_dir / "%(title)s.%(ext)s"),
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        append_log(
            log_path, "yt-dlp", "OK" if result.returncode == 0 else "FAIL",
            f"captions rc={result.returncode}"
        )
        return result.returncode == 0
    except Exception as e:
        append_log(log_path, "yt-dlp", "FAIL", str(e))
        return False


def extract_transcript(
    video_input: VideoInput,
    ctx: VideoContext,
    caps: CapabilityMap,
) -> None:
    log_path = ctx.logs_dir / "transcript.log"

    # Use existing captions if present
    existing = _find_existing_vtt(ctx.captions_dir)
    if existing:
        content = existing.read_text(encoding="utf-8", errors="replace")
        ctx.transcript_path.write_text(vtt_to_markdown(content))
        append_log(log_path, "transcript", "OK", f"from existing {existing.name}")
        return

    if not caps.yt_dlp:
        append_log(log_path, "yt-dlp", "SKIP", "not installed")
        return

    if video_input.input_type == "local_file":
        append_log(log_path, "yt-dlp", "SKIP", "local file — use Whisper instead")
        return

    _run_yt_dlp_captions(video_input.raw, ctx.captions_dir, log_path)

    existing = _find_existing_vtt(ctx.captions_dir)
    if existing:
        content = existing.read_text(encoding="utf-8", errors="replace")
        ctx.transcript_path.write_text(vtt_to_markdown(content))
        append_log(log_path, "transcript", "OK", f"from yt-dlp {existing.name}")
    else:
        append_log(log_path, "transcript", "FAIL", "no captions found after yt-dlp")
