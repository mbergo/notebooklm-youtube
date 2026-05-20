from __future__ import annotations
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs


def make_slug(index: int, title: str) -> str:
    prefix = f"{index:03d}"
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    cleaned = re.sub(r"\s+", "-", cleaned.strip()).lower()
    cleaned = cleaned[:50].rstrip("-")
    return f"{prefix}-{cleaned}"


def video_id_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")
    return None


def append_log(log_path: Path, tool: str, status: str, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{tool}][{status}] {ts} — {message}\n"
    with log_path.open("a") as f:
        f.write(line)
