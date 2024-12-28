"""Command-line interface example of using the okcourse module to generate an OK Course.

This script demonstrates how to use the okcourse module to create a course outline, generate its lectures, and
optionally generate an MP3 audio file for the course.

This script uses the asynchronous versions of the okcourse module functions. For an example that uses the synchronous
versions, see examples/cli_example.py.
"""

import asyncio
import os
import sys

import questionary

from okcourse import (
    AsyncOpenAICourseGenerator,
    default_generator_settings,
)

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

    print("Initializing course generator...")
    gen_settings = default_generator_settings
    gen_settings.output_directory = os.path.expanduser("~/.okcourse_output_new")
    gen_settings.log_to_file = True
    course_generator = AsyncOpenAICourseGenerator(gen_settings)

    topic = await async_prompt(questionary.text, "Enter a course topic:")
    if not topic or str(topic).strip() == "":
        print("No topic entered - exiting.")
        sys.exit(0)

    course_generator.settings.course_title = str(topic).strip()  # TODO: Prevent course titles about little Bobby Tables

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

        course_generator.settings.num_lectures = num_lectures

        print(f"Generating course outline with {num_lectures} lectures...")
        gen_result = await course_generator.generate_outline()
        print(str(gen_result.course.outline))
        print(os.linesep)

        proceed = await async_prompt(questionary.confirm, "Proceed with this outline?")
        if proceed:
            break

        regenerate = await async_prompt(questionary.confirm, "Generate a new outline?")
        if not regenerate:
            print("Cannot generate lecture without outline - exiting.")
            sys.exit(0)

    if await async_prompt(questionary.confirm, "Generate MP3 audio file for course?"):
        course_generator.settings.generate_audio = True
        course_generator.settings.tts_voice = await async_prompt(
            questionary.select,
            "Choose a voice for the course lecturer",
            choices=course_generator.tts_voices,
            default=course_generator.tts_voices[0],
        )

        if await async_prompt(questionary.confirm, "Generate cover image for audio file?"):
            course_generator.settings.generate_image = True

    print(f"Generating content for {course_generator.settings.num_lectures} course lectures...")
    gen_result = await course_generator.generate_lectures()

    if course_generator.settings.generate_image:
        print("Generating cover image...")
        gen_result = await course_generator.generate_image()

    if course_generator.settings.generate_audio:
        print("Generating course audio...")
        gen_result = await course_generator.generate_audio()


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
