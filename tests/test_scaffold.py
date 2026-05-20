from pathlib import Path
from scripts.scaffold import create_video_ctx_root, create_video_dirs
from scripts.models import VideoInput


def test_create_root_structure(tmp_path):
    root = tmp_path / ".video_ctx"
    create_video_ctx_root(root)
    assert (root / "videos").is_dir()
    assert (root / "raw-input").is_dir()
    assert (root / "scripts").is_dir()
    assert (root / "artifacts").is_dir()


def test_create_video_dirs(tmp_path):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(raw="https://youtu.be/abc", id_slug="001-test-video")
    create_video_dirs(root, vi)
    video_dir = root / "videos" / "001-test-video"
    for sub in ["captions", "audio", "frames", "artifacts", "logs"]:
        assert (video_dir / sub).is_dir(), f"Missing subdir: {sub}"


def test_create_video_dirs_idempotent(tmp_path):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(raw="https://youtu.be/abc", id_slug="001-test-video")
    create_video_dirs(root, vi)
    create_video_dirs(root, vi)  # second call must not raise
    assert (root / "videos" / "001-test-video").is_dir()
