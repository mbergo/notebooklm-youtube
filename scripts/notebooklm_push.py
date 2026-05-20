"""Push processed videos to NotebookLM and use it as a RAG machine.

For each video in .video_ctx/videos/:
  1. Creates a NotebookLM notebook
  2. Adds the YouTube URL as a source
  3. Waits for source indexing
  4. Asks engineering analysis questions (RAG)
  5. Generates a deep-dive audio podcast
  6. Downloads podcast to artifacts/podcast.mp3
  7. Writes all results to engineering-analysis.md and notebooklm-notes.md

Run after: uv run notebooklm login --browser-cookies chrome

Usage:
    uv run python -m scripts.notebooklm_push [--root .video_ctx] [--dry-run] [--no-podcast]
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

RAG_QUESTIONS = [
    "What is this video about? Give a 2-3 sentence summary of the core message.",
    "What are the top 5 technical concepts or engineering insights covered? List each with a one-sentence explanation.",
    "What are the most important practical takeaways for a software engineer?",
    "What tools, frameworks, languages, or technologies are mentioned or demonstrated?",
    "Are there any surprising, counterintuitive, or commonly misunderstood points raised?",
    "What prerequisite knowledge would help someone get the most from this content?",
]


def _get_url(source_md: Path) -> str | None:
    m = re.search(r"\*\*URL / Path\*\*: (.+)", source_md.read_text())
    return m.group(1).strip() if m else None


def _get_title(source_md: Path, fallback: str) -> str:
    m = re.search(r"\*\*Title\*\*: (.+)", source_md.read_text())
    t = m.group(1).strip() if m else ""
    return t if t and t != "unknown" else fallback


def _write_engineering_analysis(path: Path, title: str, url: str, qa: list[tuple[str, str]]) -> None:
    lines = [f"# Engineering Analysis: {title}\n", f"Source: {url}\n"]
    for q, a in qa:
        lines.append(f"## {q}\n\n{a}\n")
    path.write_text("\n".join(lines))


def _write_notebooklm_notes(
    path: Path, notebook_id: str, url: str, podcast_path: Path | None
) -> None:
    podcast_line = (
        f"- **Podcast**: `{podcast_path}`\n- **Play**: open the file above"
        if podcast_path and podcast_path.exists()
        else "- **Podcast**: generation failed or skipped"
    )
    path.write_text(
        f"""# NotebookLM Notes

## Notebook
- **ID**: `{notebook_id}`
- **URL**: https://notebooklm.google.com/notebook/{notebook_id}
- **Source**: {url}

## Podcast
{podcast_line}

## RAG queries
See `engineering-analysis.md` for full Q&A output.

## More queries
```bash
uv run notebooklm ask "your question" -n {notebook_id}
uv run notebooklm generate quiz -n {notebook_id}
uv run notebooklm generate mind-map -n {notebook_id}
```
"""
    )


async def process_video(
    video_dir: Path,
    client,  # NotebookLMClient
    dry_run: bool,
    no_podcast: bool,
) -> bool:
    source_md = video_dir / "source.md"
    if not source_md.exists():
        print(f"  [skip] no source.md — {video_dir.name}")
        return False

    url = _get_url(source_md)
    if not url or "youtube" not in url:
        print(f"  [skip] no YouTube URL — {video_dir.name}")
        return False

    title = _get_title(source_md, video_dir.name)
    analysis_path = video_dir / "engineering-analysis.md"
    notes_path = video_dir / "notebooklm-notes.md"
    podcast_path = video_dir / "artifacts" / "podcast.mp3"

    print(f"\n[{video_dir.name}] {title}")
    print(f"  URL: {url}")

    if dry_run:
        print("  [dry-run] would: create notebook → add source → RAG x6 → generate podcast → download")
        return True

    # 1. Create notebook
    print("  Creating notebook...")
    notebook = await client.notebooks.create(title)
    notebook_id = notebook.id
    print(f"  Notebook: {notebook_id}")

    # 2. Add YouTube source
    print("  Adding YouTube source (indexing may take 30-90s)...")
    await client.sources.add_url(notebook_id, url)
    await client.sources.wait_for_sources(notebook_id)
    print("  Source indexed.")

    # 3. RAG questions
    print("  Querying (RAG)...")
    qa: list[tuple[str, str]] = []
    for i, question in enumerate(RAG_QUESTIONS, 1):
        print(f"    Q{i}/{len(RAG_QUESTIONS)}: {question[:60]}...")
        try:
            response = await client.chat.ask(notebook_id, question)
            answer = response.text if hasattr(response, "text") else str(response)
        except Exception as e:
            answer = f"[error: {e}]"
        qa.append((question, answer))

    _write_engineering_analysis(analysis_path, title, url, qa)
    print(f"  Engineering analysis written: {analysis_path}")

    # 4. Generate podcast
    podcast_path_result: Path | None = None
    if not no_podcast:
        print("  Generating podcast (1-3 min)...")
        try:
            artifact = await client.artifacts.generate_audio(
                notebook_id,
                description="deep dive focusing on key engineering insights and technical concepts",
            )
            await client.artifacts.wait_for_completion(artifact)
            podcast_path.parent.mkdir(parents=True, exist_ok=True)
            await client.artifacts.download_audio(notebook_id, str(podcast_path))
            podcast_path_result = podcast_path
            print(f"  Podcast saved: {podcast_path}")
        except Exception as e:
            print(f"  [warn] podcast failed: {e}")

    _write_notebooklm_notes(notes_path, notebook_id, url, podcast_path_result)
    print(f"  Notes written: {notes_path}")
    return True


async def run(root: Path, dry_run: bool, no_podcast: bool) -> None:
    from notebooklm import NotebookLMClient

    videos_dir = root / "videos"
    video_dirs = sorted(d for d in videos_dir.iterdir() if d.is_dir())
    if not video_dirs:
        print(f"No videos in {videos_dir}")
        return

    print(f"Found {len(video_dirs)} video(s)")

    if dry_run:
        for d in video_dirs:
            await process_video(d, None, dry_run=True, no_podcast=no_podcast)
        return

    async with await NotebookLMClient.from_storage() as client:
        results = []
        for d in video_dirs:
            ok = await process_video(d, client, dry_run=False, no_podcast=no_podcast)
            results.append(ok)

    ok_count = sum(results)
    print(f"\nDone: {ok_count}/{len(results)} videos pushed to NotebookLM")


def main() -> None:
    parser = argparse.ArgumentParser(description="NotebookLM RAG push for processed videos")
    parser.add_argument("--root", default=".video_ctx")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-podcast", action="store_true", help="Skip podcast generation")
    args = parser.parse_args()

    asyncio.run(run(Path(args.root), args.dry_run, args.no_podcast))


if __name__ == "__main__":
    main()
