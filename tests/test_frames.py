from pathlib import Path
from unittest.mock import call
from scripts.frames import build_baseline_ffmpeg_cmd, build_dense_ffmpeg_cmd, extract_frames
from scripts.models import VideoContext, VideoInput, CapabilityMap


def test_build_baseline_ffmpeg_cmd(tmp_path):
    input_file = tmp_path / "video.mp4"
    frames_dir = tmp_path / "frames"
    cmd = build_baseline_ffmpeg_cmd(input_file, frames_dir)
    assert cmd[0] == "ffmpeg"
    assert "-hide_banner" in cmd
    assert "fps=1/30,scale=960:-1" in " ".join(cmd)
    assert str(frames_dir / "frame_%05d.jpg") in cmd


def test_build_dense_ffmpeg_cmd(tmp_path):
    input_file = tmp_path / "video.mp4"
    frames_dir = tmp_path / "frames"
    cmd = build_dense_ffmpeg_cmd(input_file, frames_dir, start="00:02:10", end="00:04:30", label="intro")
    assert "-ss" in cmd
    assert "00:02:10" in cmd
    assert "-to" in cmd
    assert "00:04:30" in cmd
    assert "fps=1/5,scale=1280:-1" in " ".join(cmd)
    assert "important_intro_" in " ".join(cmd)


def test_extract_frames_skips_when_ffmpeg_missing(tmp_path, mocker):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(raw="https://youtu.be/abc", id_slug="001-test")
    ctx = VideoContext(root=root, id_slug="001-test")
    ctx.frames_dir.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)
    mock_run = mocker.patch("subprocess.run")
    extract_frames(vi, ctx, caps=CapabilityMap(ffmpeg=False), video_file=None)
    mock_run.assert_not_called()


def test_extract_frames_skips_when_no_video_file(tmp_path, mocker):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(raw="https://youtu.be/abc", id_slug="001-test")
    ctx = VideoContext(root=root, id_slug="001-test")
    ctx.frames_dir.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)
    mock_run = mocker.patch("subprocess.run")
    extract_frames(vi, ctx, caps=CapabilityMap(ffmpeg=True), video_file=None)
    mock_run.assert_not_called()


def test_extract_frames_calls_ffmpeg(tmp_path, mocker):
    root = tmp_path / ".video_ctx"
    vi = VideoInput(raw="https://youtu.be/abc", id_slug="001-test")
    ctx = VideoContext(root=root, id_slug="001-test")
    ctx.frames_dir.mkdir(parents=True, exist_ok=True)
    ctx.logs_dir.mkdir(parents=True, exist_ok=True)
    video_file = tmp_path / "video.mp4"
    video_file.write_bytes(b"fake")
    mock_run = mocker.patch(
        "subprocess.run",
        return_value=mocker.MagicMock(returncode=0),
    )
    extract_frames(vi, ctx, caps=CapabilityMap(ffmpeg=True), video_file=video_file)
    assert mock_run.called
    cmd = mock_run.call_args[0][0]
    assert "ffmpeg" in cmd
