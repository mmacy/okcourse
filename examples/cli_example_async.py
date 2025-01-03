# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "questionary>=2.1.0",
#     "okcourse@git+https://github.com/mmacy/okcourse",
# ]
# ///
import asyncio
import os
import sys
from pathlib import Path

import questionary

from okcourse import Course, OpenAIAsyncGenerator
from okcourse.models import CourseGenerationDetails
from okcourse.utils import sanitize_filename


class OpenAIPricing:
    """Class to store and manage OpenAI pricing details."""
    GPT4O_INPUT_COST_PER_1K_TOKENS = 0.00250
    GPT4O_OUTPUT_COST_PER_1K_TOKENS = 0.01000
    TTS_COST_PER_1K_CHARACTERS = 0.015
    DALLE_COST_PER_IMAGE = 0.040


def calculate_openai_cost(details: CourseGenerationDetails) -> dict[str, float]:
    """Calculates the costs based on token and character counts using the OpenAI pricing.

    OpenAI pricing as of 2024-01-02:
        - GPT-4o: $0.00250 / 1K input tokens
        - GPT-4o: $0.01000 / 1K output tokens
        - DALL-E-3: $0.040 / image (Standard 1024×1024)
        - TTS-1: $0.015 / 1K characters

    Args:
        details (CourseGenerationDetails): The course generation details containing usage data.

    Returns:
        dict[str, float]: A dictionary with cost breakdown and total cost.
    """
    input_token_cost = (details.input_token_count / 1000) * OpenAIPricing.GPT4O_INPUT_COST_PER_1K_TOKENS
    output_token_cost = (details.output_token_count / 1000) * OpenAIPricing.GPT4O_OUTPUT_COST_PER_1K_TOKENS
    tts_cost = (details.tts_character_count / 1000) * OpenAIPricing.TTS_COST_PER_1K_CHARACTERS
    image_cost = details.num_images_generated * OpenAIPricing.DALLE_COST_PER_IMAGE

    total_cost = input_token_cost + output_token_cost + tts_cost + image_cost

    return {
        "input_token_cost": round(input_token_cost, 4),
        "output_token_cost": round(output_token_cost, 4),
        "tts_cost": round(tts_cost, 4),
        "image_cost": round(image_cost, 4),
        "total_cost": round(total_cost, 4),
    }


async def async_prompt(prompt_func, *args, **kwargs):
    """Runs a sync questionary prompt in separate thread and returns the result asynchronously.

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
    print("============================")
    print("==  okcourse CLI (async)  ==")
    print("============================")

    course = Course()
    course.settings.output_directory = os.path.expanduser("~/.okcourse_files")
    course.settings.log_to_file = True

    topic = await async_prompt(questionary.text, "Enter a course topic:")
    if not topic or str(topic).strip() == "":
        print("No topic entered - exiting.")
        sys.exit(0)
    course.title = str(topic).strip()  # TODO: Prevent course titles about little Bobby Tables

    generator = OpenAIAsyncGenerator(course)

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

    do_generate_audio = False
    do_generate_image = False
    if await async_prompt(questionary.confirm, "Generate MP3 audio file for course?"):
        do_generate_audio = True
        course.settings.tts_voice = await async_prompt(
            questionary.select,
            "Choose a voice for the course lecturer",
            choices=generator.tts_voices,
            default=generator.tts_voices[0],
        )

        if await async_prompt(questionary.confirm, "Generate cover image for audio file?"):
            do_generate_image = True

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

    if do_generate_image:
        print("Generating cover image...")
        course = await generator.generate_image(course)

    if do_generate_audio:
        print("Generating course audio...")
        course = await generator.generate_audio(course)

    # Done with generation - save the course to JSON now that it's fully populated
    json_file_out = course.settings.output_directory / Path(sanitize_filename(course.title)).with_suffix(".json")
    json_file_out.write_text(course.model_dump_json(indent=2))
    print(f"Course JSON file saved to {json_file_out}")
    print(f"Done! Course file(s) available in {course.settings.output_directory}")
    print(os.linesep)
    print(f"Generation details:\n{course.details.model_dump_json(indent=2)}")
    print(os.linesep)
    print(f"Cost breakdown:\n{calculate_openai_cost(course.details)}")

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
