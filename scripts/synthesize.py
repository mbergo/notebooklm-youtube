from __future__ import annotations
from pathlib import Path
from typing import List

from scripts.models import VideoContext, VideoInput


def write_index_md(
    root: Path,
    inputs: List[VideoInput],
    contexts: List[VideoContext],
) -> None:
    lines = ["# Video Context Index\n", "| # | Slug | URL | Transcript | Frames |\n",
             "|---|------|-----|-----------|--------|\n"]
    for vi, ctx in zip(inputs, contexts):
        has_transcript = "yes" if ctx.transcript_path.exists() else "no"
        has_frames = "yes" if any(ctx.frames_dir.glob("*.jpg")) else "no"
        lines.append(f"| {vi.playlist_index or ''} | {vi.id_slug} | {vi.raw} | {has_transcript} | {has_frames} |\n")
    (root / "index.md").write_text("".join(lines))


def _global_stub(path: Path, header: str, sections: List[str]) -> None:
    if path.exists() and path.stat().st_size > 100:
        return
    lines = [f"# {header}\n"]
    for section in sections:
        lines.append(f"## {section}\n*(fill after per-video analysis complete)*\n")
    path.write_text("\n".join(lines))


def write_global_stubs(
    root: Path,
    inputs: List[VideoInput],
    contexts: List[VideoContext],
) -> None:
    write_index_md(root, inputs, contexts)

    _global_stub(
        root / "global-summary.md",
        "Global Summary",
        ["Cross-video summary", "Recurring themes", "Strongest insights",
         "Weakest claims", "Practical takeaways"],
    )
    _global_stub(
        root / "cross-video-engineering-analysis.md",
        "Cross-Video Engineering Analysis",
        ["Repeated concepts", "Architecture patterns", "Tool comparisons",
         "Implementation opportunities", "Risks and tradeoffs",
         "Contradictions", "What matters for this repository"],
    )
    _global_stub(
        root / "combined-implementation-plan.md",
        "Combined Implementation Plan",
        ["P0 backlog", "P1 backlog", "P2 backlog", "Grouped workstreams",
         "Risk register", "Test strategy", "Next 30 minutes",
         "Next 1 day", "Next 1 week"],
    )
    _global_stub(
        root / "open-questions.md",
        "Open Questions",
        ["Unresolved questions", "Research tasks", "Assumptions to validate",
         "Missing tools / data"],
    )

    readme = root / "README.md"
    if not readme.exists():
        slugs = "\n".join(f"- `videos/{vi.id_slug}/`" for vi in inputs)
        readme.write_text(f"""# .video_ctx — Video Research Context Pack

## Purpose
Structured local evidence extracted from {len(inputs)} video(s).

## Videos processed
{slugs}

## How to add more videos
```bash
uv run python scripts/pipeline.py --input "https://youtu.be/NEW_ID"
```

## How to regenerate
```bash
uv run python scripts/pipeline.py --input urls.txt
```

## What NOT to commit
See `.gitignore` — audio/, video files, frames/, tokens, cookies.
""")
