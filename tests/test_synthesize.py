from pathlib import Path
from scripts.synthesize import write_index_md, write_global_stubs
from scripts.models import VideoInput, VideoContext


def _make_inputs_and_contexts(tmp_path, count=2):
    root = tmp_path / ".video_ctx"
    inputs = []
    contexts = []
    for i in range(1, count + 1):
        vi = VideoInput(raw=f"https://youtu.be/{i:03d}", id_slug=f"{i:03d}-video-{i}")
        ctx = VideoContext(root=root, id_slug=f"{i:03d}-video-{i}")
        ctx.video_dir.mkdir(parents=True, exist_ok=True)
        (ctx.video_dir / "source.md").write_text(f"# Source {i}")
        inputs.append(vi)
        contexts.append(ctx)
    return root, inputs, contexts


def test_write_index_md(tmp_path):
    root, inputs, contexts = _make_inputs_and_contexts(tmp_path, 2)
    write_index_md(root, inputs, contexts)
    content = (root / "index.md").read_text()
    assert "001-video-1" in content
    assert "002-video-2" in content


def test_write_global_stubs_creates_files(tmp_path):
    root, inputs, contexts = _make_inputs_and_contexts(tmp_path, 1)
    write_global_stubs(root, inputs, contexts)
    for fname in [
        "index.md",
        "global-summary.md",
        "cross-video-engineering-analysis.md",
        "combined-implementation-plan.md",
        "open-questions.md",
        "README.md",
    ]:
        assert (root / fname).exists(), f"Missing: {fname}"


def test_write_global_stubs_idempotent(tmp_path):
    root, inputs, contexts = _make_inputs_and_contexts(tmp_path, 1)
    write_global_stubs(root, inputs, contexts)
    write_global_stubs(root, inputs, contexts)
    assert (root / "index.md").exists()
