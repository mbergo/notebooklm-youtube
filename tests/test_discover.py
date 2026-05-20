from pathlib import Path
from unittest.mock import patch
from scripts.discover import discover_capabilities, write_missing_tools_report
from scripts.models import CapabilityMap


def test_discover_all_present(tmp_path, mocker):
    mocker.patch("shutil.which", side_effect=lambda cmd: f"/usr/bin/{cmd}")
    caps = discover_capabilities(log_path=tmp_path / "run-log.md")
    assert caps.yt_dlp is True
    assert caps.ffmpeg is True
    assert caps.whisper is True


def test_discover_all_missing(tmp_path, mocker):
    mocker.patch("shutil.which", return_value=None)
    caps = discover_capabilities(log_path=tmp_path / "run-log.md")
    assert caps.yt_dlp is False
    assert caps.ffmpeg is False
    assert caps.whisper is False
    assert caps.notebooklm is False


def test_discover_logs_missing_tools(tmp_path, mocker):
    mocker.patch("shutil.which", return_value=None)
    log = tmp_path / "run-log.md"
    discover_capabilities(log_path=log)
    content = log.read_text()
    assert "yt-dlp" in content
    assert "MISSING" in content


def test_write_missing_tools_report(tmp_path):
    caps = CapabilityMap(yt_dlp=False, ffmpeg=True, whisper=False, notebooklm=False)
    report = tmp_path / "missing-tools.md"
    write_missing_tools_report(report, caps)
    content = report.read_text()
    assert "yt-dlp" in content
    assert "whisper" in content
    assert "ffmpeg" not in content.lower().replace("ffmpeg", "FFMPEG_PRESENT")


def test_notebooklm_detected_via_subprocess(tmp_path, mocker):
    mocker.patch("shutil.which", side_effect=lambda cmd: "/usr/local/bin/notebooklm" if cmd == "notebooklm" else None)
    mocker.patch("subprocess.run", return_value=mocker.MagicMock(returncode=0))
    caps = discover_capabilities(log_path=tmp_path / "run-log.md")
    assert caps.notebooklm is True
