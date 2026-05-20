from scripts.models import VideoInput, CapabilityMap, VideoContext


def test_video_input_defaults():
    vi = VideoInput(raw="https://youtu.be/abc123", id_slug="001-abc123")
    assert vi.raw == "https://youtu.be/abc123"
    assert vi.id_slug == "001-abc123"
    assert vi.input_type == "url"
    assert vi.playlist_index is None


def test_capability_map_defaults():
    cm = CapabilityMap()
    assert cm.yt_dlp is False
    assert cm.ffmpeg is False
    assert cm.whisper is False
    assert cm.notebooklm is False


def test_video_context_root_path(tmp_path):
    vc = VideoContext(root=tmp_path, id_slug="001-test")
    assert vc.video_dir == tmp_path / "videos" / "001-test"
    assert vc.transcript_path == tmp_path / "videos" / "001-test" / "transcript.md"
    assert vc.frames_dir == tmp_path / "videos" / "001-test" / "frames"
    assert vc.captions_dir == tmp_path / "videos" / "001-test" / "captions"
    assert vc.logs_dir == tmp_path / "videos" / "001-test" / "logs"
