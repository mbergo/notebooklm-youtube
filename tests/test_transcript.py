from pathlib import Path
from scripts.transcript import vtt_to_markdown, extract_transcript
from scripts.models import VideoInput, CapabilityMap, VideoContext

_SAMPLE_VTT = """\
WEBVTT

00:00:01.000 --> 00:00:03.500
Hello world

00:00:03.500 --> 00:00:05.000
Hello world

00:00:05.000 --> 00:00:08.000
This is a test transcript.
"""


def test_vtt_to_markdown_deduplicates():
    md = vtt_to_markdown(_SAMPLE_VTT)
    assert md.count("Hello world") == 1


def test_vtt_to_markdown_preserves_timestamps():
    md = vtt_to_markdown(_SAMPLE_VTT)
    assert "00:00:01" in md


def test_vtt_to_markdown_strips_webvtt_header():
    md = vtt_to_markdown(_SAMPLE_VTT)
    assert "WEBVTT" not in md


def test_vtt_to_markdown_includes_content():
    md = vtt_to_markdown(_SAMPLE_VTT)
    assert "This is a test transcript." in md


def test_extract_transcript_uses_existing_vtt(tmp_path, mocker):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(raw="https://youtu.be/abc", id_slug="001-test")
    ctx = VideoContext(root=root, id_slug="001-test")
    ctx.captions_dir.mkdir(parents=True, exist_ok=True)
    vtt_file = ctx.captions_dir / "captions.en.vtt"
    vtt_file.write_text(_SAMPLE_VTT)
    # Should NOT call yt-dlp if vtt already exists
    mock_run = mocker.patch("subprocess.run")
    extract_transcript(vi, ctx, caps=CapabilityMap(yt_dlp=True))
    mock_run.assert_not_called()
    assert ctx.transcript_path.exists()


def test_extract_transcript_calls_yt_dlp_when_no_captions(tmp_path, mocker):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(raw="https://youtu.be/abc", id_slug="001-test")
    ctx = VideoContext(root=root, id_slug="001-test")
    ctx.captions_dir.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)
    mock_run = mocker.patch(
        "subprocess.run",
        return_value=mocker.MagicMock(returncode=0, stdout="", stderr=""),
    )
    extract_transcript(vi, ctx, caps=CapabilityMap(yt_dlp=True))
    assert mock_run.called
    call_args = mock_run.call_args[0][0]
    assert "yt-dlp" in call_args


def test_extract_transcript_skips_when_no_yt_dlp(tmp_path):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(raw="https://youtu.be/abc", id_slug="001-test")
    ctx = VideoContext(root=root, id_slug="001-test")
    ctx.captions_dir.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)
    # Should not raise even if yt-dlp missing
    extract_transcript(vi, ctx, caps=CapabilityMap(yt_dlp=False))
    # transcript.md may or may not exist; no exception is the requirement
