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
    Course,
    CourseSettings,
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

    course_settings = CourseSettings()
    course_settings.output_directory = os.path.expanduser("~/.okcourse_files")
    course_settings.log_to_file = True
    course = Course(settings=course_settings)

    topic = await async_prompt(questionary.text, "Enter a course topic:")
    if not topic or str(topic).strip() == "":
        print("No topic entered - exiting.")
        sys.exit(0)
    course.title = str(topic).strip()  # TODO: Prevent course titles about little Bobby Tables

    generator = OpenAIAsyncGenerator(course)

    if await async_prompt(questionary.confirm, "Generate course using default settings?"):
        print(f"Generating course with {course.settings.num_lectures} lectures...")
        course = await generator.generate_course(course)
        print(os.linesep)
        print(f"Done! Course file(s) saved to {course.settings.output_directory}")
        sys.exit(0)

    while True:
        course.settings.num_lectures = await async_prompt(
            questionary.text,
            "How many lectures should be in the course?",
            default=str(course.settings.num_lectures),
        )
        try:
            course.settings.num_lectures = int(course.settings.num_lectures)
            if course.settings.num_lectures <= 0:
                print("There must be at least one (1) lecture in the series.")
                continue  # Input is invalid
        except ValueError:
            print("Enter a valid number greater than 0.")
            continue  # Input is invalid
        break  # Input is valid - exit loop

    if await async_prompt(questionary.confirm, "Generate MP3 audio file for course?"):
        course.settings.generate_audio = True
        course.settings.tts_voice = await async_prompt(
            questionary.select,
            "Choose a voice for the course lecturer",
            choices=generator.tts_voices,
            default=generator.tts_voices[0],
        )

        if await async_prompt(questionary.confirm, "Generate cover image for audio file?"):
            course.settings.generate_image = True

        out_dir = await async_prompt(
            questionary.text,
            "Enter a directory for the course output:",
            default=course.settings.output_directory,
        )
        course.settings.output_directory = Path(out_dir)

    while True:
        print(f"Generating course outline with {course.settings.num_lectures} lectures...")
        course = await generator.generate_outline(course)
        print(str(course.outline))
        print(os.linesep)

        proceed = await async_prompt(questionary.confirm, "Proceed with this outline?")
        if proceed:
            break

        regenerate = await async_prompt(questionary.confirm, "Generate a new outline?")
        if not regenerate:
            print("Cannot generate lecture without outline - exiting.")
            sys.exit(0)

    print(f"Generating content for {course.settings.num_lectures} course lectures...")
    course = await generator.generate_lectures(course)

    if course.settings.generate_image:
        print("Generating cover image...")
        course = await generator.generate_image(course)

    if course.settings.generate_audio:
        print("Generating course audio...")
        course = await generator.generate_audio(course)

    print(f"Done! Course file(s) saved to {course.settings.output_directory}")


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
