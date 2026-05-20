from pathlib import Path
from scripts.analyze import write_source_md, write_summary_stub, write_per_video_stubs
from scripts.models import VideoInput, VideoContext


def _make_ctx(tmp_path):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(
        raw="https://youtu.be/abc123",
        id_slug="001-test-video",
        title="Test Video",
    )
    ctx = VideoContext(root=root, id_slug="001-test-video")
    ctx.video_dir.mkdir(parents=True, exist_ok=True)
    return vi, ctx


def test_write_source_md(tmp_path):
    vi, ctx = _make_ctx(tmp_path)
    write_source_md(vi, ctx, tools_used=["yt-dlp"], tools_failed=["whisper"])
    content = (ctx.video_dir / "source.md").read_text()
    assert "https://youtu.be/abc123" in content
    assert "yt-dlp" in content
    assert "whisper" in content


def test_write_summary_stub(tmp_path):
    vi, ctx = _make_ctx(tmp_path)
    write_summary_stub(vi, ctx, transcript_excerpt="Hello world test content.")
    content = (ctx.video_dir / "summary.md").read_text()
    assert "summary" in content.lower()
    assert "Hello world" in content


def test_write_per_video_stubs_creates_all_files(tmp_path):
    vi, ctx = _make_ctx(tmp_path)
    write_per_video_stubs(vi, ctx, tools_used=["yt-dlp"], tools_failed=[])
    for fname in [
        "source.md", "summary.md", "engineering-analysis.md",
        "implementation-plan.md", "questions.md", "confidence.md",
        "notebooklm-notes.md", "visual-notes.md",
    ]:
        assert (ctx.video_dir / fname).exists(), f"Missing: {fname}"


def test_write_per_video_stubs_idempotent(tmp_path):
    vi, ctx = _make_ctx(tmp_path)
    write_per_video_stubs(vi, ctx, tools_used=[], tools_failed=[])
    write_per_video_stubs(vi, ctx, tools_used=[], tools_failed=[])
    # No exception; existing files not overwritten if already have content
    assert (ctx.video_dir / "source.md").exists()
