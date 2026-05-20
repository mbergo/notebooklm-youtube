from pathlib import Path
from scripts.utils import make_slug, append_log, video_id_from_url


def test_make_slug_basic():
    assert make_slug(1, "How I Built a Thing") == "001-how-i-built-a-thing"


def test_make_slug_strips_special_chars():
    assert make_slug(2, "AI: 100% Guide!") == "002-ai-100-guide"


def test_make_slug_truncates_long_titles():
    long = "a" * 100
    slug = make_slug(1, long)
    assert len(slug) <= 60


def test_video_id_from_url_standard():
    assert video_id_from_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_video_id_from_url_short():
    assert video_id_from_url("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_video_id_from_url_non_youtube():
    assert video_id_from_url("https://vimeo.com/123456") is None


def test_append_log_creates_file(tmp_path):
    log_file = tmp_path / "run-log.md"
    append_log(log_file, "yt-dlp", "OK", "captions downloaded")
    content = log_file.read_text()
    assert "[yt-dlp][OK]" in content
    assert "captions downloaded" in content


def test_append_log_appends(tmp_path):
    log_file = tmp_path / "run-log.md"
    append_log(log_file, "ffmpeg", "FAIL", "not found")
    append_log(log_file, "whisper", "SKIP", "no audio")
    lines = log_file.read_text().splitlines()
    assert len(lines) == 2
