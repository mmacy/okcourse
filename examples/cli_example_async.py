"""Command-line interface example of using the okcourse module to generate an OK Course.

This script demonstrates how to use the okcourse module to create a course outline, generate its lectures, and
optionally generate an MP3 audio file for the course.

This script uses the asynchronous versions of the okcourse module functions. For an example that uses the synchronous
versions, see examples/cli_example.py.
"""

import asyncio
import os
import sys
from pathlib import Path

import questionary

from okcourse import (
    CourseGeneratorSettings,
    OpenAIAsyncGenerator,
)


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

    settings = CourseGeneratorSettings()
    settings.output_directory = os.path.expanduser("~/.okcourse_files")
    settings.log_to_file = True
    generator = OpenAIAsyncGenerator(settings)

    topic = await async_prompt(questionary.text, "Enter a course topic:")
    if not topic or str(topic).strip() == "":
        print("No topic entered - exiting.")
        sys.exit(0)

    generator.settings.course_title = str(topic).strip()  # TODO: Prevent course titles about little Bobby Tables

    if await async_prompt(questionary.confirm, "Generate course using default settings?"):
        print(f"Generating course with {generator.settings.num_lectures} lectures...")
        result = await generator.generate_course()
        print(os.linesep)
        print(f"Done! Course file(s) saved to {result.settings.output_directory}")
        sys.exit(0)

    generator.settings.num_lectures = await async_prompt(
        questionary.text, f"How many lectures should be in the course (default: {generator.settings.num_lectures})?"
    )

    if await async_prompt(questionary.confirm, "Generate MP3 audio file for course?"):
        generator.settings.generate_audio = True
        generator.settings.tts_voice = await async_prompt(
            questionary.select,
            "Choose a voice for the course lecturer",
            choices=generator.tts_voices,
            default=generator.tts_voices[0],
        )

        if await async_prompt(questionary.confirm, "Generate cover image for audio file?"):
            generator.settings.generate_image = True

        out_dir = await async_prompt(
            questionary.text,
            "Enter a directory for the course output:",
            default=settings.output_directory,
        )
        settings.output_directory = Path(out_dir)

    while True:
        print(f"Generating course outline with {generator.settings.num_lectures} lectures...")
        result = await generator.generate_outline()
        print(str(result.course.outline))
        print(os.linesep)

        proceed = await async_prompt(questionary.confirm, "Proceed with this outline?")
        if proceed:
            break

        regenerate = await async_prompt(questionary.confirm, "Generate a new outline?")
        if not regenerate:
            print("Cannot generate lecture without outline - exiting.")
            sys.exit(0)

    print(f"Generating content for {generator.settings.num_lectures} course lectures...")
    result = await generator.generate_lectures()

    if generator.settings.generate_image:
        print("Generating cover image...")
        result = await generator.generate_image()

    if generator.settings.generate_audio:
        print("Generating course audio...")
        result = await generator.generate_audio()

    print(f"Done! Course file(s) saved to {result.settings.output_directory}")


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
