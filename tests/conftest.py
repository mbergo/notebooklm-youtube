import pytest
from pathlib import Path


@pytest.fixture
def video_ctx_root(tmp_path):
    """Returns a temp .video_ctx root with subdirs."""
    root = tmp_path / ".video_ctx"
    root.mkdir()
    return root
