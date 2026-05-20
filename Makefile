.PHONY: help install test lint run push dry-run clean

INPUT ?=

help:
	@echo "Targets:"
	@echo "  install          uv sync"
	@echo "  test             run pytest"
	@echo "  lint             ruff check + ruff format --check"
	@echo "  run INPUT=<url>  run pipeline on URL/file"
	@echo "  push             push processed videos to NotebookLM"
	@echo "  dry-run          preview push without executing"
	@echo "  clean            remove .video_ctx output"

install:
	uv sync

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check scripts/ tests/
	uv run ruff format --check scripts/ tests/

run:
	@[ -n "$(INPUT)" ] || (echo "ERROR: INPUT is required. make run INPUT=https://youtu.be/ID" && exit 1)
	uv run python -m scripts.pipeline --input "$(INPUT)"

run-no-frames:
	@[ -n "$(INPUT)" ] || (echo "ERROR: INPUT is required." && exit 1)
	uv run python -m scripts.pipeline --input "$(INPUT)" --no-frames

push:
	uv run python -m scripts.notebooklm_push

push-no-podcast:
	uv run python -m scripts.notebooklm_push --no-podcast

dry-run:
	uv run python -m scripts.notebooklm_push --dry-run

clean:
	rm -rf .video_ctx
