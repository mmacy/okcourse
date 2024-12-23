"""Command-line interface example of using the okcourse module to generate an OK Course.

This script demonstrates how to use the okcourse module to create a course outline, generate its lectures, and
optionally generate an MP3 audio file for the course.

This script uses the asynchronous versions of the okcourse module functions. For an example that uses the synchronous
versions, see examples/cli_example.py.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import aiofiles
import questionary

from okcourse import (
    TTS_VOICES,
    configure_logging,
    generate_course_audio_async,
    generate_course_image_async,
    generate_course_lectures_async,
    generate_course_outline_async,
    sanitize_filename,
)

configure_logging(logging.INFO)

num_lectures_default = 10
# 20 lectures yields approx. 1:40:00 MP3
# 10 lectures yields approx. 0:45:00 MP3


async def async_prompt(prompt_func, *args, **kwargs):
    """Runs a synchronous questionary prompt in a separate thread and returns the result asynchronously.

    Args:
        prompt_func: The questionary prompt function (e.g., questionary.text).
        *args: Positional arguments for the prompt function.
        **kwargs: Keyword arguments for the prompt function.

    Returns:
        The result of the prompt.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: prompt_func(*args, **kwargs).ask())


async def main():
    print("=======================")
    print("==  OK Course Maker  ==")
    print("=======================")

    topic = await async_prompt(questionary.text, "Enter a course topic:")
    if not topic:
        print("No topic entered - exiting.")
        sys.exit(0)

    while True:
        num_lectures_input = await async_prompt(
            questionary.text, f"How many lectures should be in the course (default: {num_lectures_default})?"
        )

        if not num_lectures_input:
            num_lectures = num_lectures_default
        else:
            try:
                num_lectures = int(num_lectures_input)
                if num_lectures <= 0:
                    print("There must be at least one (1) lecture in the series.")
                    continue
            except ValueError:
                print("Enter a valid number greater than 0.")
                continue

        print(f"Generating course outline with {num_lectures} lectures...")
        outline = await generate_course_outline_async(topic, num_lectures)
        print(str(outline))
        print(os.linesep)

        proceed = await async_prompt(questionary.confirm, "Proceed with this outline?")
        if proceed:
            break

        regenerate = await async_prompt(questionary.confirm, "Generate a new outline?")
        if not regenerate:
            print("Cannot generate lecture without outline - exiting.")
            sys.exit(0)

    print("Generating course text...")
    course = await generate_course_lectures_async(outline)

    # Set up some default paths
    output_dir = Path.cwd() / "generated_okcourses"
    output_file_base = output_dir / sanitize_filename(course.title)
    output_file_json = output_file_base.with_suffix(".json")
    output_file_mp3 = output_file_base.with_suffix(".mp3")
    output_file_png = output_file_base.with_suffix(".png")

    async with aiofiles.open(output_file_json, "w", encoding="utf-8") as f:
        await f.write(course.model_dump_json(indent=2))
        print(f"Saved course JSON to {str(output_file_json)}")

    if await async_prompt(questionary.confirm, "Generate MP3 audio file for course?"):
        tts_voice = await async_prompt(
            questionary.select, "Choose a voice for the course lecturer", choices=TTS_VOICES, default=TTS_VOICES[0]
        )

        # YES they want AUDIO - do they also want a COVER IMAGE?
        if await async_prompt(questionary.confirm, "Generate cover image for audio file?"):
            print("Generating cover image...")

            # YES they want a COVER IMAGE - get the PNG
            await generate_course_image_async(
                course_outline=course.outline,
                image_file_path=output_file_png,
            )
            if output_file_png.exists():
                print(f"Cover image generated: {str(output_file_png)}")

        print("Generating course audio...")
        course_audio_path = await generate_course_audio_async(
            course,
            output_file_mp3,
            tts_voice,
            cover_image_path=output_file_png if output_file_png.exists() else None,
        )
        print(f"Course audio: {str(course_audio_path)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            # Handle cases where the event loop is already running, like in debuggers or interactive environments
            loop = asyncio.get_event_loop()
            task = loop.create_task(main())
            loop.run_until_complete(task)
        else:
            raise
