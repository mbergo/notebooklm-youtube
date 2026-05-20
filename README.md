# notebooklm-youtube — Video Research Pipeline

Reusable local pipeline for turning YouTube videos into structured engineering evidence.

## Mental model

```
yt-dlp    = source collector
FFmpeg    = eyeballs
Whisper   = emergency ears
NotebookLM = optional prosthetic brain (fragile — never the spine)
Claude Code = engineer/synthesizer
.video_ctx  = durable memory palace
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- ffmpeg (already installed via linuxbrew)

## Setup

```bash
uv sync
uv run yt-dlp --version   # verify
```

## Usage

```bash
# Single video
uv run python scripts/pipeline.py --input "https://youtu.be/VIDEO_ID"

# Playlist
uv run python scripts/pipeline.py --input "https://youtube.com/playlist?list=PLxxx"

# Text file of URLs
uv run python scripts/pipeline.py --input urls.txt

# Skip frames (faster)
uv run python scripts/pipeline.py --input "https://youtu.be/VIDEO_ID" --no-frames
```

Or use the Claude Code slash command:
```
/video-research-pipeline
Input: https://youtu.be/VIDEO_ID
```

## Output structure

```
.video_ctx/
  index.md                          ← all videos + status
  missing-tools.md                  ← what to install
  run-log.md                        ← tool execution log
  global-summary.md                 ← cross-video insights
  cross-video-engineering-analysis.md
  combined-implementation-plan.md
  open-questions.md
  videos/
    001-video-slug/
      source.md                     ← provenance + quality
      transcript.md                 ← clean timestamped transcript
      summary.md                    ← TL;DR + detailed summary
      engineering-analysis.md       ← Staff engineer extraction
      implementation-plan.md        ← P0/P1/P2 backlog
      questions.md                  ← open questions
      confidence.md                 ← evidence quality
      notebooklm-notes.md           ← NotebookLM Q&A
      visual-notes.md               ← frame analysis
      captions/                     ← raw .vtt/.srt files
      audio/                        ← (gitignored) wav for Whisper
      frames/                       ← (gitignored) extracted jpegs
```

## Optional: NotebookLM

```bash
pip install 'notebooklm-py[browser]'
notebooklm login
uv run python scripts/pipeline.py --input "..."
```

## Tests

```bash
uv run pytest tests/ -v
```
