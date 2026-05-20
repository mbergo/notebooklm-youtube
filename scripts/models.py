from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional


@dataclass
class VideoInput:
    raw: str
    id_slug: str
    input_type: Literal["url", "local_file"] = "url"
    playlist_index: Optional[int] = None
    title: Optional[str] = None


@dataclass
class CapabilityMap:
    yt_dlp: bool = False
    ffmpeg: bool = False
    whisper: bool = False
    notebooklm: bool = False
    python: bool = True


@dataclass
class VideoContext:
    root: Path
    id_slug: str

    @property
    def video_dir(self) -> Path:
        return self.root / "videos" / self.id_slug

    @property
    def transcript_path(self) -> Path:
        return self.video_dir / "transcript.md"

    @property
    def frames_dir(self) -> Path:
        return self.video_dir / "frames"

    @property
    def captions_dir(self) -> Path:
        return self.video_dir / "captions"

    @property
    def logs_dir(self) -> Path:
        return self.video_dir / "logs"

    @property
    def audio_dir(self) -> Path:
        return self.video_dir / "audio"

    @property
    def artifacts_dir(self) -> Path:
        return self.video_dir / "artifacts"
