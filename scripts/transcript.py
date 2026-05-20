from __future__ import annotations
import re
import subprocess
from pathlib import Path
from typing import List

from scripts.models import CapabilityMap, VideoContext, VideoInput
from scripts.utils import append_log


def _strip_vtt_tags(text: str) -> str:
    """Remove inline VTT timing/karaoke tags and normalize whitespace."""
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


_YT_CHECKPOINT_THRESHOLD_MS = 200  # YouTube auto-caption checkpoint cues are ≤ ~10ms


def _ts_to_ms(ts: str) -> int:
    """Convert HH:MM:SS.mmm or MM:SS.mmm (WebVTT) to milliseconds."""
    ts = ts.strip()
    try:
        parts = ts.split(":")
        if len(parts) == 3:
            h, m, rest = parts
        elif len(parts) == 2:
            h, m, rest = "0", parts[0], parts[1]
        else:
            return 0
        s, ms = rest.split(".")
        return (
            int(h) * 3_600_000
            + int(m) * 60_000
            + int(s) * 1_000
            + int(ms.ljust(3, "0")[:3])
        )
    except ValueError:
        return 0


# VTT metadata lines that YouTube injects as cue text
_VTT_META = re.compile(r"^(Kind|Language|WEBVTT)\s*:", re.IGNORECASE)


def vtt_to_markdown(vtt_content: str) -> str:
    lines = vtt_content.splitlines()

    # Collect raw cues: (start_ms, duration_ms, [text_lines])
    cues: List[tuple[int, int, List[str]]] = []
    start_ms = 0
    duration_ms = 0
    text_lines: List[str] = []

    def _flush() -> None:
        if text_lines:
            cues.append((start_ms, duration_ms, list(text_lines)))
        text_lines.clear()

    for line in lines:
        line = line.strip()
        if not line or line == "WEBVTT" or line.startswith("NOTE"):
            _flush()
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}", line) and "-->" in line:
            _flush()
            parts = line.split("-->")
            start_ms = _ts_to_ms(parts[0])
            end_ms = _ts_to_ms(parts[1].split()[0])  # strip cue settings
            duration_ms = end_ms - start_ms
            continue
        if re.match(r"^\d+$", line):
            continue
        text_lines.append(line)

    _flush()

    # YouTube auto-captions pattern:
    #   Long cues (~2-4s): rolling window — first line = previous text, last line = new karaoke
    #   Short cues (<200ms): checkpoint — single clean completed line
    # Strategy: prefer checkpoint cues; fall back to last line of long cues when no checkpoint follows.
    entries: List[tuple[str, str]] = []
    for start_ms, dur_ms, tlines in cues:
        # Skip blank / metadata-only cues
        cleaned = [_strip_vtt_tags(l) for l in tlines]
        cleaned = [l for l in cleaned if l and not _VTT_META.match(l)]
        if not cleaned:
            continue

        ts = f"{start_ms // 3_600_000:02d}:{(start_ms % 3_600_000) // 60_000:02d}:{(start_ms % 60_000) // 1000:02d}.{start_ms % 1000:03d}"

        if 0 <= dur_ms < _YT_CHECKPOINT_THRESHOLD_MS:
            # Checkpoint cue — take all lines joined
            entries.append((ts, " ".join(cleaned)))
        else:
            # Rolling cue — take only the LAST line (new content)
            entries.append((ts, cleaned[-1]))

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
    except subprocess.TimeoutExpired:
        append_log(log_path, "yt-dlp", "FAIL", "timeout after 120s")
        return False
    except OSError as e:
        append_log(log_path, "yt-dlp", "FAIL", f"OS error: {e}")
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
