from __future__ import annotations
from pathlib import Path
from scripts.models import VideoInput

_ROOT_SUBDIRS = ["videos", "raw-input", "scripts", "artifacts"]
_VIDEO_SUBDIRS = ["captions", "audio", "frames", "artifacts", "logs"]


def create_video_ctx_root(root: Path) -> None:
    for sub in _ROOT_SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)


def create_video_dirs(root: Path, video_input: VideoInput) -> None:
    video_dir = root / "videos" / video_input.id_slug
    for sub in _VIDEO_SUBDIRS:
        (video_dir / sub).mkdir(parents=True, exist_ok=True)
