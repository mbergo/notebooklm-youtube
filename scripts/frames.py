from __future__ import annotations
import subprocess
from pathlib import Path
from typing import List, Optional

from scripts.models import CapabilityMap, VideoContext, VideoInput
from scripts.utils import append_log


def build_baseline_ffmpeg_cmd(input_file: Path, frames_dir: Path) -> List[str]:
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-i", str(input_file),
        "-vf", "fps=1/30,scale=960:-1",
        str(frames_dir / "frame_%05d.jpg"),
    ]


def build_dense_ffmpeg_cmd(
    input_file: Path,
    frames_dir: Path,
    start: str,
    end: str,
    label: str,
) -> List[str]:
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-ss", start,
        "-to", end,
        "-i", str(input_file),
        "-vf", "fps=1/5,scale=1280:-1",
        str(frames_dir / f"important_{label}_%05d.jpg"),
    ]


def extract_frames(
    video_input: VideoInput,
    ctx: VideoContext,
    caps: CapabilityMap,
    video_file: Optional[Path],
) -> None:
    log_path = ctx.logs_dir / "frames.log"

    if not caps.ffmpeg:
        append_log(log_path, "ffmpeg", "SKIP", "not installed")
        return

    if video_file is None or not video_file.exists():
        append_log(log_path, "ffmpeg", "SKIP", "no video file available")
        return

    ctx.frames_dir.mkdir(parents=True, exist_ok=True)
    cmd = build_baseline_ffmpeg_cmd(video_file, ctx.frames_dir)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        status = "OK" if result.returncode == 0 else "FAIL"
        append_log(log_path, "ffmpeg", status, f"baseline frames rc={result.returncode}")
    except Exception as e:
        append_log(log_path, "ffmpeg", "FAIL", str(e))
