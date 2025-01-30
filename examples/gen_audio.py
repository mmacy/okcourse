# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "okcourse",
#     "pydantic",
#     "rich",
#     "click",
# ]
# ///

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from okcourse import Course, OpenAIAsyncGenerator
from okcourse.utils.log_utils import get_logger


_log = None

console = Console()


def load_courses_from_directory(directory: Path) -> list[Course]:
    """Loads Course objects from all JSON files in the specified directory."""
    courses = []
    _log.info(f"Scanning directory: {directory}")
    for json_file in directory.glob("*.json"):
        try:
            with json_file.open("r", encoding="utf-8") as file:
                course_data = json.load(file)
                _log.debug(f"Loading course from {json_file.name}")
                course = Course.model_validate(course_data)
                courses.append(course)
        except (json.JSONDecodeError, ValidationError) as exc:
            _log.error(f"Error loading {json_file.name}: {exc}")
    return courses


async def generate_audio_for_course(course: Course, output_dir: Path) -> None:
    """Generates audio files for the given course using OpenAIAsyncGenerator."""
    _log.info(f"Generating audio for course: {course.title}")
    generator = OpenAIAsyncGenerator(course)

    try:
        await generator.generate_audio(course)
    except Exception as e:
        _log.error(f"Failed to generate audio for course: {e}")
        return

    if course.generation_info.audio_file_path and course.generation_info.audio_file_path.exists():
        _log.info(f"TTS audio generated and saved to: {course.generation_info.audio_file_path}")
    else:
        _log.warning(f"TTS audio generated but audio file not found at {course.generation_info.audio_file_path}")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "directory",
    type=click.Path(
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        path_type=Path,
    ),
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output for debugging purposes.",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        writable=True,
        path_type=Path,
    ),
    default=None,
    help="Directory to save the generated audio files. Defaults to the input directory.",
)
def main(directory: Path, verbose: bool, output_dir: Optional[Path]) -> None:
    """Generate TTS audio files from an okcourse JSON file.

    This script scans the specified DIRECTORY for JSON files, attempts to load Course
    objects from them, and then allows you to select a course for which to generate
    audio using a TTS model.
    """
    global _log
    _log = get_logger("gen_audio", logging.DEBUG if verbose else logging.INFO)

    output_dir = output_dir or directory
    output_dir.mkdir(parents=True, exist_ok=True)
    _log.debug(f"Output directory set to: {output_dir}")

    courses = load_courses_from_directory(directory)
    if not courses:
        _log.error("No valid courses found in the specified directory. Exiting.")
        sys.exit(1)

    table = Table()
    table.add_column("Index", justify="center", style="cyan", no_wrap=True)
    table.add_column("Course title", style="magenta")
    for idx, course in enumerate(courses, start=1):
        table.add_row(str(idx), course.title)
    console.print(table)

    selected_course = (
        courses[0]
        if len(courses) == 1
        else courses[
            click.prompt(
                f"Select a course to generate audio for (1 to {len(courses)})", type=click.IntRange(1, len(courses))
            )
            - 1
        ]
    )
    _log.info(f"Selected course: {selected_course.title}")

    asyncio.run(generate_audio_for_course(selected_course, output_dir))


if __name__ == "__main__":
    main()
