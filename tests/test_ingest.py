from pathlib import Path
from unittest.mock import patch, MagicMock
import json
from scripts.ingest import classify_input, normalize_inputs, InputType

def test_classify_single_url():
    result = classify_input("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert result == InputType.SINGLE_URL

def test_classify_playlist_url():
    result = classify_input("https://www.youtube.com/playlist?list=PLrEnWoR732-BHrPp_Pm8_VleD68f9s14")
    assert result == InputType.PLAYLIST_URL

def test_classify_text_file(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("https://youtu.be/aaa\nhttps://youtu.be/bbb\n")
    result = classify_input(str(f))
    assert result == InputType.TEXT_FILE

def test_classify_local_video(tmp_path):
    f = tmp_path / "video.mp4"
    f.write_bytes(b"fake")
    result = classify_input(str(f))
    assert result == InputType.LOCAL_FILE

def test_classify_multi_url_string():
    result = classify_input("https://youtu.be/aaa\nhttps://youtu.be/bbb")
    assert result == InputType.MULTI_URL

def test_normalize_single_url():
    inputs = normalize_inputs("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert len(inputs) == 1
    assert inputs[0].raw == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert inputs[0].id_slug.startswith("001-")

def test_normalize_text_file(tmp_path):
    f = tmp_path / "urls.txt"
    f.write_text("https://youtu.be/aaa\nhttps://youtu.be/bbb\nhttps://youtu.be/aaa\n")
    inputs = normalize_inputs(str(f))
    # deduplication: aaa appears twice → 2 unique
    assert len(inputs) == 2
    assert inputs[0].id_slug.startswith("001-")
    assert inputs[1].id_slug.startswith("002-")

def test_normalize_local_file(tmp_path):
    f = tmp_path / "talk.mp4"
    f.write_bytes(b"fake")
    inputs = normalize_inputs(str(f))
    assert len(inputs) == 1
    assert inputs[0].input_type == "local_file"
    assert inputs[0].raw == str(f)

def test_normalize_playlist_url(mocker):
    mock_entries = [
        {"webpage_url": "https://youtu.be/aaa", "title": "Video A"},
        {"webpage_url": "https://youtu.be/bbb", "title": "Video B"},
    ]
    mocker.patch(
        "scripts.ingest._fetch_playlist_entries",
        return_value=mock_entries,
    )
    inputs = normalize_inputs("https://www.youtube.com/playlist?list=PLtest")
    assert len(inputs) == 2
    assert inputs[0].id_slug == "001-video-a"
    assert inputs[1].id_slug == "002-video-b"
