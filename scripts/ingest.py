from __future__ import annotations
import json
import re
import subprocess
from enum import Enum, auto
from pathlib import Path
from typing import List

from scripts.models import VideoInput
from scripts.utils import make_slug, video_id_from_url

_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v", ".flv"}


class InputType(Enum):
    SINGLE_URL = auto()
    MULTI_URL = auto()
    PLAYLIST_URL = auto()
    TEXT_FILE = auto()
    LOCAL_FILE = auto()
    TOPIC = auto()


def classify_input(raw: str) -> InputType:
    path = Path(raw)
    if path.exists() and path.is_file():
        if path.suffix.lower() in _VIDEO_EXTENSIONS:
            return InputType.LOCAL_FILE
        return InputType.TEXT_FILE
    if "playlist?list=" in raw or "/playlist?" in raw:
        return InputType.PLAYLIST_URL
    urls = [line.strip() for line in raw.splitlines() if line.strip().startswith("http")]
    if len(urls) > 1:
        return InputType.MULTI_URL
    if raw.strip().startswith("http"):
        return InputType.SINGLE_URL
    return InputType.TOPIC


def _fetch_playlist_entries(playlist_url: str) -> list[dict]:
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings", playlist_url],
        capture_output=True,
        text=True,
        timeout=60,
    )
    entries = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def _deduplicate(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for url in urls:
        norm = url.strip()
        vid_id = video_id_from_url(norm) or norm
        if vid_id not in seen:
            seen.add(vid_id)
            out.append(norm)
    return out


def normalize_inputs(raw: str) -> List[VideoInput]:
    input_type = classify_input(raw)

    if input_type == InputType.LOCAL_FILE:
        path = Path(raw).resolve()
        slug = make_slug(1, path.stem)
        return [VideoInput(raw=str(path), id_slug=slug, input_type="local_file")]

    if input_type == InputType.TEXT_FILE:
        lines = Path(raw).read_text().splitlines()
        urls = _deduplicate([l.strip() for l in lines if l.strip().startswith("http")])
        return [
            VideoInput(raw=url, id_slug=make_slug(i + 1, url.split("/")[-1]))
            for i, url in enumerate(urls)
        ]

    if input_type == InputType.MULTI_URL:
        urls = _deduplicate([l.strip() for l in raw.splitlines() if l.strip().startswith("http")])
        return [
            VideoInput(raw=url, id_slug=make_slug(i + 1, url.split("/")[-1]))
            for i, url in enumerate(urls)
        ]

    if input_type == InputType.PLAYLIST_URL:
        entries = _fetch_playlist_entries(raw)
        results = []
        for i, entry in enumerate(entries):
            url = entry.get("webpage_url", entry.get("url", ""))
            title = entry.get("title", url.split("/")[-1])
            results.append(VideoInput(
                raw=url,
                id_slug=make_slug(i + 1, title),
                playlist_index=i + 1,
                title=title,
            ))
        return results

    # SINGLE_URL
    url = raw.strip()
    slug = make_slug(1, url.split("/")[-1])
    return [VideoInput(raw=url, id_slug=slug)]
