# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "questionary>=2.1.0",
#     "okcourse",
# ]
# ///
import asyncio
import os
import sys
from pathlib import Path

import questionary

from okcourse import Course, OpenAIAsyncGenerator
from okcourse.generators.openai.openai_utils import tts_voices, get_usable_models_async
from okcourse.prompt_library import PROMPT_COLLECTION
from okcourse.utils.text_utils import sanitize_filename, get_duration_string_from_seconds


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
    course.settings.output_directory = Path("~/.okcourse_files").expanduser().resolve()
    course.settings.log_to_file = True

    prompt_options = {prompt.description: prompt for prompt in PROMPT_COLLECTION}
    selected_prompt_name = await async_prompt(
        questionary.select,
        "Choose a course type",
        choices=list(prompt_options.keys()),
        # default=list(prompt_options.keys()),
    )
    selected_prompt = prompt_options[selected_prompt_name]
    course.settings.prompts = selected_prompt

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
        course.settings.num_subtopics = await async_prompt(
            questionary.text,
            "How many sub-topics per lecture?",
            default=str(course.settings.num_subtopics),
        )
        try:
            course.settings.num_lectures = int(course.settings.num_lectures)
            course.settings.num_subtopics = int(course.settings.num_subtopics)
            if course.settings.num_lectures <= 0:
                print("There must be at least one (1) lecture in the series.")
                continue  # Input is invalid
            if course.settings.num_subtopics <= 0:
                print("There must be at least one (1) sub-topic per lecture.")
                continue
        except ValueError:
            print("Enter a valid number greater than 0.")
            continue  # Input is invalid
        break  # Input is valid - exit loop

    models = await get_usable_models_async()
    models.text_models.sort()
    course.settings.text_model_lecture = await async_prompt(
        questionary.select,
        "Choose a model to generate the course outline and lectures",
        choices=models.text_models,
        default=models.text_models[-1],
    )

    out_dir = await async_prompt(
        questionary.text,
        "Enter a directory for the course output:",
        default=str(course.settings.output_directory),
    )
    course.settings.output_directory = Path(out_dir)

    outline_accepted = False
    while True:
        print(f"Generating course outline with {course.settings.num_lectures} lectures...")
        course = await generator.generate_outline(course)
        print(str(course.outline))
        print(os.linesep)

        proceed = await async_prompt(questionary.confirm, "Proceed with this outline?")
        if proceed:
            outline_accepted = True
            break

        regenerate = await async_prompt(questionary.confirm, "Generate a new outline?")
        if not regenerate:
            print("No lectures will be generated.")
            break

    lectures_accepted = False
    while outline_accepted:
        print(f"Generating content for {course.settings.num_lectures} course lectures...")
        course = await generator.generate_lectures(course)
        print(str(course))

        if await async_prompt(questionary.confirm, "Continue with these lectures?"):
            lectures_accepted = True
            break  # Exit loop to move on to generate image and/or audio
        else:
            if await async_prompt(questionary.confirm, "Generate new lectures?"):
                continue  # Stay in the loop and generate another batch of lectures

            else:
                break  # Exit loop with !lectures_accepted

    if lectures_accepted and await async_prompt(questionary.confirm, "Generate cover image for course?"):
        print("Generating cover image...")
        course = await generator.generate_image(course)

    if lectures_accepted and await async_prompt(questionary.confirm, "Generate MP3 audio file for course?"):
        course.settings.tts_voice = await async_prompt(
            questionary.select,
            "Choose a voice for the course lecturer",
            choices=tts_voices,
            default=tts_voices[0],
        )

        print("Generating course audio...")
        course = await generator.generate_audio(course)

    total_generation_time = get_duration_string_from_seconds(
        course.generation_info.outline_gen_elapsed_seconds
        + course.generation_info.lecture_gen_elapsed_seconds
        + course.generation_info.image_gen_elapsed_seconds
        + course.generation_info.audio_gen_elapsed_seconds
    )

    # Done with generation - save the course to JSON now that it's fully populated
    json_file_out = course.settings.output_directory / Path(sanitize_filename(course.title)).with_suffix(".json")
    json_file_out.write_text(course.model_dump_json(indent=2))
    print(f"Course JSON file saved to {json_file_out}")
    print(f"Done! Course generated in {total_generation_time}. File(s) available in {course.settings.output_directory}")
    print(f"Generation details:\n{course.generation_info.model_dump_json(indent=2)}")


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
