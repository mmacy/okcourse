# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`okcourse` is a Python library that generates audiobook-style courses with lectures on any topic using AI models (text completion, text-to-speech, and image generation). Given a course title, it generates an outline, lecture text, cover art, and audio file.

## Development commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_string_utils.py::test_split_text_into_chunks_short_text

# Run example CLI app
uv run examples/cli_example_async.py

# Serve documentation locally
uv sync --group docs
uv run mkdocs serve
```

## Architecture

### Core data flow

```
Title → Outline → Lectures → Cover Image → Audio File
```

All course content is contained in the `Course` Pydantic model, which holds settings, outline, lectures, and generation metadata.

### Key modules

- `src/okcourse/models.py` - Pydantic models: `Course`, `CourseSettings`, `CourseOutline`, `CourseLecture`, `CoursePromptSet`
- `src/okcourse/generators/base.py` - Abstract `CourseGenerator` base class defining the generation interface
- `src/okcourse/generators/openai/async_openai.py` - `OpenAIAsyncGenerator` implementation using OpenAI's API
- `src/okcourse/prompt_library.py` - Predefined prompt sets (`ACADEMIC`, `GAME_MASTER`) that control course style
- `src/okcourse/utils/` - Utilities for text splitting, audio processing, and logging

### Generator pattern

Generators inherit from `CourseGenerator` and implement four abstract methods:

- `generate_outline()` - Creates course structure from title
- `generate_lectures()` - Generates lecture text for each topic
- `generate_image()` - Creates cover art
- `generate_audio()` - Converts lectures to speech and combines into MP3

The `OpenAIAsyncGenerator` uses async/await and `asyncio.TaskGroup` for concurrent API calls.

### Prompt system

Courses are styled via `CoursePromptSet` objects containing system, outline, lecture, and image prompts with `${variable}` placeholders. The default `ACADEMIC` prompt creates graduate-level lecture content; `GAME_MASTER` creates RPG adventure narrations.

## Environment

Requires `OPENAI_API_KEY` environment variable for API access.

## Package structure

```
src/okcourse/
├── __init__.py          # Public API exports
├── models.py            # Pydantic data models
├── constants.py         # Constants (AI_DISCLOSURE, MAX_LECTURES)
├── prompt_library.py    # Predefined prompt sets
├── generators/
│   ├── base.py          # Abstract CourseGenerator
│   └── openai/
│       ├── async_openai.py   # OpenAI implementation
│       └── openai_utils.py   # Retry logic, rate limiting
└── utils/
    ├── text_utils.py    # Text chunking, tokenization
    ├── audio_utils.py   # MP3 combining, ID3 tagging
    └── log_utils.py     # Logging setup
```
