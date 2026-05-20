from __future__ import annotations
from pathlib import Path
from typing import List

from scripts.models import VideoContext, VideoInput


def write_source_md(
    video_input: VideoInput,
    ctx: VideoContext,
    tools_used: List[str],
    tools_failed: List[str],
) -> None:
    out = ctx.video_dir / "source.md"
    content = f"""# Source: {video_input.id_slug}

## Input
- **URL / Path**: {video_input.raw}
- **Type**: {video_input.input_type}
- **Title**: {video_input.title or "unknown"}
- **Playlist index**: {video_input.playlist_index or "N/A"}

## Processing
- **Tools used**: {", ".join(tools_used) if tools_used else "none"}
- **Tools failed**: {", ".join(tools_failed) if tools_failed else "none"}

## Evidence quality
- Transcript: see transcript.md
- Visual: see visual-notes.md
- NotebookLM: see notebooklm-notes.md
"""
    out.write_text(content)


def write_summary_stub(
    video_input: VideoInput,
    ctx: VideoContext,
    transcript_excerpt: str = "",
) -> None:
    out = ctx.video_dir / "summary.md"
    if out.exists() and out.stat().st_size > 200:
        return
    content = f"""# Summary: {video_input.id_slug}

## TL;DR
*(10-line summary — fill after reading transcript)*

## Transcript excerpt (first 500 chars)
{transcript_excerpt[:500]}

## Detailed summary
*(fill after analysis)*

## Main thesis
*(fill)*

## Notable claims
*(fill)*
"""
    out.write_text(content)


def _stub(path: Path, header: str, sections: List[str]) -> None:
    if path.exists() and path.stat().st_size > 100:
        return
    lines = [f"# {header}\n"]
    for section in sections:
        lines.append(f"## {section}\n*(fill)*\n")
    path.write_text("\n".join(lines))


def write_per_video_stubs(
    video_input: VideoInput,
    ctx: VideoContext,
    tools_used: List[str],
    tools_failed: List[str],
) -> None:
    ctx.video_dir.mkdir(parents=True, exist_ok=True)

    write_source_md(video_input, ctx, tools_used, tools_failed)

    transcript_excerpt = ""
    if ctx.transcript_path.exists():
        transcript_excerpt = ctx.transcript_path.read_text()[:500]
    write_summary_stub(video_input, ctx, transcript_excerpt)

    _stub(
        ctx.video_dir / "engineering-analysis.md",
        f"Engineering Analysis: {video_input.id_slug}",
        [
            "Technical concepts", "Tools / frameworks / APIs mentioned",
            "Architecture patterns", "Data flow", "System boundaries",
            "Security implications", "Performance implications",
            "What is useful for this project", "What is hype or vague",
        ],
    )
    _stub(
        ctx.video_dir / "implementation-plan.md",
        f"Implementation Plan: {video_input.id_slug}",
        ["P0 tasks", "P1 tasks", "P2 tasks", "Dependencies", "Risks",
         "Next 30 minutes", "Next 1 day", "Next 1 week"],
    )
    _stub(
        ctx.video_dir / "questions.md",
        f"Questions: {video_input.id_slug}",
        ["Questions for speaker", "Research tasks", "Assumptions to verify",
         "Missing context", "Contradictions"],
    )
    _stub(
        ctx.video_dir / "confidence.md",
        f"Confidence: {video_input.id_slug}",
        ["Transcript confidence", "Visual confidence", "NotebookLM confidence",
         "Unresolved uncertainties"],
    )
    _stub(
        ctx.video_dir / "notebooklm-notes.md",
        f"NotebookLM Notes: {video_input.id_slug}",
        ["What is the video about", "Main thesis", "Strongest technical claims",
         "Tools / frameworks mentioned", "Architecture patterns",
         "Implementation tasks", "Vague / unsupported claims"],
    )
    _stub(
        ctx.video_dir / "visual-notes.md",
        f"Visual Notes: {video_input.id_slug}",
        ["Frame inventory", "Diagrams / slides found", "Code / commands visible",
         "UI walkthroughs", "Charts / tables"],
    )
