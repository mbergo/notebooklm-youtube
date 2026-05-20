from __future__ import annotations
import shutil
import subprocess
from pathlib import Path

from scripts.models import CapabilityMap
from scripts.utils import append_log

_TOOL_COMMANDS = {
    "yt_dlp": "yt-dlp",
    "ffmpeg": "ffmpeg",
    "whisper": "whisper",
    "notebooklm": "notebooklm",
}


def discover_capabilities(log_path: Path) -> CapabilityMap:
    caps = CapabilityMap()
    for attr, cmd in _TOOL_COMMANDS.items():
        found = shutil.which(cmd) is not None
        if attr == "notebooklm" and found:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    timeout=5,
                )
                found = result.returncode == 0
            except Exception:
                found = False
        setattr(caps, attr, found)
        status = "OK" if found else "MISSING"
        append_log(log_path, cmd, status, f"which={shutil.which(cmd)}")
    return caps


def write_missing_tools_report(report_path: Path, caps: CapabilityMap) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Missing Tools\n"]
    missing = []
    install_hints = {
        "yt-dlp": "uv run pip install yt-dlp  # or: uv add yt-dlp",
        "whisper": "uv run pip install openai-whisper",
        "notebooklm": (
            "pip install 'notebooklm-py[browser]'\n"
            "notebooklm login  # requires interactive browser auth\n"
            "notebooklm list   # verify auth works"
        ),
    }
    checks = [
        ("yt-dlp", caps.yt_dlp),
        ("whisper", caps.whisper),
        ("notebooklm", caps.notebooklm),
    ]
    for name, present in checks:
        if not present:
            missing.append(name)
            hint = install_hints.get(name, f"Install {name}")
            lines.append(f"## {name}\n\nStatus: MISSING\n\nInstall:\n```\n{hint}\n```\n")
    if not missing:
        lines.append("All tools present.\n")
    report_path.write_text("".join(lines))
