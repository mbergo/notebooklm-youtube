# notebooklm-youtube — Video Research Pipeline

Reusable local pipeline for turning YouTube videos into structured engineering evidence.

## Mental model

```
yt-dlp      = source collector
FFmpeg      = eyeballs
Whisper     = emergency ears
NotebookLM  = RAG machine (create notebooks, ask questions, generate podcasts)
Claude Code = engineer/synthesizer
.video_ctx  = durable memory palace
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- `ffmpeg` on PATH (optional — skipped gracefully if missing)
- `yt-dlp` on PATH (installed via `uv sync`)

## Setup

```bash
git clone https://github.com/youruser/notebooklm-youtube
cd notebooklm-youtube
uv sync
uv run yt-dlp --version   # verify
```

## Usage

Always invoke as a module (`python -m`), never as a file path:

```bash
# Single video
uv run python -m scripts.pipeline --input "https://youtu.be/VIDEO_ID"

# Playlist
uv run python -m scripts.pipeline --input "https://youtube.com/playlist?list=PLxxx"

# Text file of URLs
uv run python -m scripts.pipeline --input urls.txt

# Local video file
uv run python -m scripts.pipeline --input /path/to/video.mp4

# Skip FFmpeg (faster — transcript only)
uv run python -m scripts.pipeline --input "https://youtu.be/VIDEO_ID" --no-frames
```

Or use the Claude Code slash command:
```
/video-research-pipeline
Input: https://youtu.be/VIDEO_ID
```

## NotebookLM integration

Adds YouTube sources to NotebookLM, runs 6 RAG questions per video, and generates a deep-dive audio podcast.

### One-time auth

```bash
uv sync --extra cookies           # install rookiepy for cookie import
uv run notebooklm login --browser-cookies chrome
```

### Push all processed videos

```bash
uv run python -m scripts.notebooklm_push           # all videos in .video_ctx/
uv run python -m scripts.notebooklm_push --dry-run  # preview only
uv run python -m scripts.notebooklm_push --no-podcast
```

Outputs per video:
- `engineering-analysis.md` — 6-question RAG Q&A
- `notebooklm-notes.md` — notebook ID, URL, podcast link
- `artifacts/podcast.mp3` — deep-dive audio podcast

## Output structure

```
.video_ctx/
  index.md                              ← all videos + status
  missing-tools.md                      ← what to install
  run-log.md                            ← tool execution log
  global-summary.md                     ← cross-video insights
  videos/
    001-video-slug/
      source.md                         ← provenance + quality
      transcript.md                     ← clean deduplicated transcript
      summary.md                        ← TL;DR
      engineering-analysis.md           ← RAG Q&A from NotebookLM
      implementation-plan.md            ← P0/P1/P2 backlog
      questions.md                      ← open questions
      confidence.md                     ← evidence quality
      notebooklm-notes.md               ← notebook ID, podcast link
      visual-notes.md                   ← frame analysis stubs
      captions/                         ← raw .vtt files
      frames/                           ← (gitignored) extracted jpegs
      artifacts/                        ← podcast.mp3, generated files
```

## Tests

```bash
uv run pytest tests/ -v
uv run pytest tests/test_transcript.py -v   # single module
uv run pytest -k "test_vtt"                 # single test
```

## Makefile shortcuts

```bash
make run INPUT="https://youtu.be/VIDEO_ID"
make push
make test
make lint
```
