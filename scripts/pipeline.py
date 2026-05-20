"""
Video Research Pipeline — main entrypoint.

Usage:
    uv run python scripts/pipeline.py --input URL_OR_FILE [--no-frames] [--no-notebooklm] [--root DIR]
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from scripts.discover import discover_capabilities, write_missing_tools_report
from scripts.ingest import normalize_inputs
from scripts.scaffold import create_video_ctx_root, create_video_dirs
from scripts.transcript import extract_transcript
from scripts.frames import extract_frames
from scripts.analyze import write_per_video_stubs
from scripts.synthesize import write_global_stubs
from scripts.models import VideoContext
from scripts.utils import append_log


def run_pipeline(
    raw_input: str,
    root: Path,
    no_frames: bool = False,
    no_notebooklm: bool = False,
) -> None:
    # 1. Capability discovery
    log_path = root / "run-log.md"
    root.mkdir(parents=True, exist_ok=True)
    caps = discover_capabilities(log_path=log_path)
    write_missing_tools_report(root / "missing-tools.md", caps)

    # 2. Scaffold root
    create_video_ctx_root(root)

    # 3. Normalize inputs
    inputs = normalize_inputs(raw_input)
    print(f"[pipeline] {len(inputs)} input(s) detected.")

    contexts = []
    tools_used_global = []
    tools_failed_global = []

    for vi in inputs:
        print(f"[pipeline] Processing: {vi.id_slug}")
        create_video_dirs(root, vi)
        ctx = VideoContext(root=root, id_slug=vi.id_slug)
        contexts.append(ctx)

        tools_used: list[str] = []
        tools_failed: list[str] = []

        # 4. Transcript
        extract_transcript(vi, ctx, caps)
        if ctx.transcript_path.exists():
            tools_used.append("yt-dlp-captions")
        else:
            tools_failed.append("captions")

        # 5. Frames
        if not no_frames and caps.ffmpeg:
            video_file = Path(vi.raw) if vi.input_type == "local_file" else None
            extract_frames(vi, ctx, caps, video_file=video_file)
            if ctx.frames_dir.exists() and any(ctx.frames_dir.iterdir()):
                tools_used.append("ffmpeg")
            else:
                tools_failed.append("ffmpeg")
        else:
            if no_frames:
                append_log(log_path, "ffmpeg", "SKIP", "--no-frames flag")
            else:
                tools_failed.append("ffmpeg")

        # 6. Per-video stubs
        write_per_video_stubs(vi, ctx, tools_used=tools_used, tools_failed=tools_failed)

        tools_used_global.extend(tools_used)
        tools_failed_global.extend(tools_failed)

    # 7. Global synthesis
    write_global_stubs(root, inputs, contexts)

    # 8. Final report
    print(f"\n{'='*60}")
    print(f"Pipeline complete.")
    print(f"  Inputs:  {len(inputs)}")
    print(f"  Videos:  {len(contexts)}")
    print(f"  Tools used:   {sorted(set(tools_used_global))}")
    print(f"  Tools failed: {sorted(set(tools_failed_global))}")
    print(f"  Output: {root}/")
    print(f"  Next: review {root}/index.md")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Video Research Pipeline")
    parser.add_argument("--input", required=True, help="URL, playlist URL, text file, or local video file")
    parser.add_argument("--root", default=".video_ctx", help="Output root directory (default: .video_ctx)")
    parser.add_argument("--no-frames", action="store_true", help="Skip FFmpeg frame extraction")
    parser.add_argument("--no-notebooklm", action="store_true", help="Skip NotebookLM")
    args = parser.parse_args()

    run_pipeline(
        raw_input=args.input,
        root=Path(args.root),
        no_frames=args.no_frames,
        no_notebooklm=args.no_notebooklm,
    )


if __name__ == "__main__":
    main()
