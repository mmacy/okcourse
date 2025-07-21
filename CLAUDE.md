# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development environment

- **Install dependencies**: `uv sync --all-groups` (installs main, dev, and docs dependencies)
- **Run tests**: `pytest` or `uv run pytest`
- **Run single test**: `pytest tests/test_filename.py::test_function_name`
- **Run example apps**:
  - CLI example: `uv run examples/cli_example_async.py`
  - Streamlit app: `uv run streamlit run examples/streamlit_example.py`
  - FastAPI web app: `uv run uvicorn examples.web_app.main:app --reload` (enhanced with markdown, auto-progression, media display)

### Documentation

- **Build docs**: `uv run mkdocs build`
- **Serve docs locally**: `uv run mkdocs serve`
- **Generate API reference**: `uv run python scripts/gen_ref_docs.py`

### Package management

- **Build package**: `uv build`
- **Install in development mode**: `uv pip install -e .`

### Requirements

- Python 3.12+ required
- OpenAI API key must be set in `OPENAI_API_KEY` environment variable
- Uses `uv` as the primary package manager

## Architecture

### Core workflow

OKCourse generates audiobook-style courses through a 4-step pipeline:
1. **Outline generation**: Course title → structured course outline with lecture topics
2. **Lecture generation**: Each topic → full lecture text (processed in parallel)
3. **Image generation**: Course title + prompts → cover art PNG file
4. **Audio generation**: Combined lecture text → chunked TTS → merged MP3 with metadata

### Key classes and data flow

- **`Course`**: Central container holding all course content and settings
- **`CourseGenerator`**: Abstract base class defining the generation interface
- **`OpenAIAsyncGenerator`**: Concrete implementation using OpenAI APIs with async concurrency
- **`CourseSettings`**: Configuration for models, prompts, output paths, and generation behavior
- **Pydantic models**: All data structures use Pydantic for validation and serialization

### Generator pattern

The library uses an abstract generator pattern (`CourseGenerator`) with four required methods:
- `generate_outline()`, `generate_lectures()`, `generate_image()`, `generate_audio()`
This allows for different AI provider implementations while maintaining a consistent interface.

### Prompt management

- Template-based prompting using Python's `string.Template`
- Domain-specific prompt sets in `prompt_library.py` (ACADEMIC, TECHNICAL, GAME_MASTER, etc.)
- Each prompt set includes system, outline, lecture, and image generation prompts

### Async concurrency

- Uses `asyncio.TaskGroup` for parallel lecture generation
- Parallel TTS processing for audio chunks while maintaining order
- Includes exponential backoff for API rate limiting

## Project structure

### Source code (`src/okcourse/`)

- **`models.py`**: Pydantic data models for courses, settings, and generation metadata
- **`prompt_library.py`**: Template-based prompt management with domain-specific sets
- **`generators/base.py`**: Abstract base class defining the generator interface
- **`generators/openai/async_openai.py`**: OpenAI implementation with async processing
- **`utils/`**: Utility modules for text processing, audio handling, and logging

### Examples and documentation

- **`examples/`**: CLI, Streamlit, and FastAPI example applications
  - **`cli_example_async.py`**: Interactive command-line interface
  - **`streamlit_example.py`**: Simple web GUI with step-by-step workflow
  - **`web_app/`**: Full-featured FastAPI application with automatic progression, markdown rendering, and media integration
- **`docs/`**: MkDocs documentation source files
- **`tests/`**: Minimal unit tests for core utilities and models

### Configuration files

- **`pyproject.toml`**: Project metadata, dependencies, and build configuration
- **`pytest.ini`**: Test configuration with short traceback format
- **`mkdocs.yml`**: Documentation site configuration with Material theme

## Development patterns

### Error handling

- API calls include retry logic with exponential backoff
- Validation for course parameters (max lectures, required fields)
- Graceful handling of rate limits and API errors with detailed logging

### Testing approach

- Minimal unit tests focusing on core utilities and data models
- Example applications serve as integration tests
- Uses pytest with short traceback format for cleaner output

### Code organization

- Clear separation between data models, generation logic, and utilities
- Heavy use of Pydantic for data validation and JSON serialization
- Async-first design for handling AI API latency efficiently

## Coding style

### General guidelines

- Use sentence case for all headings and heading-like text
- Surroung all headings, lists (ordered and unordered), code blocks, and admonitions with blank lines
