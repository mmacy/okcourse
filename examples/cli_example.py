"""Command-line interface example of using the okcourse module to generate an OK Course.

This script demonstrates how to use the okcourse module to create a course outline, generate its lectures, and
optionally generate an MP3 audio file for the course.

This script uses the synchronous versions of the okcourse module functions. For an example that uses the asynchronous
versions, see examples/cli_example_async.py.
"""

import os
import sys
from pathlib import Path

import questionary

from okcourse import (
    TTS_VOICES,
    generate_course_audio,
    generate_course_image,
    generate_course_lectures,
    generate_course_outline,
    sanitize_filename,
)

num_lectures_default = 10
# 20 lectures yields approx. 1:40:00 MP3
# 10 lectures yields approx. 0:45:00 MP3


def main():
    print("=======================")
    print("==  OK Course Maker  ==")
    print("=======================")

    topic = questionary.text("Enter a course topic:").ask()
    if not topic:
        print("No topic entered - exiting.")
        sys.exit(0)

    while True:
        num_lectures_input = questionary.text(
            f"How many lectures should be in the course (default: {num_lectures_default})?"
        ).ask()

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
        outline = generate_course_outline(topic, num_lectures)
        print(os.linesep)
        print(str(outline))
        print(os.linesep)

        proceed = questionary.confirm("Proceed with this outline?").ask()
        if proceed:
            break

        regenerate = questionary.confirm("Generate a new outline?").ask()
        if not regenerate:
            print("Cannot generate lecture without outline - exiting.")
            sys.exit(0)

    output_dir = Path.cwd() / "generated_okcourses"
    output_file_base = output_dir / sanitize_filename(outline.title)
    output_file_mp3 = output_file_base.with_suffix(".mp3")
    output_file_json = output_file_base.with_suffix(".json")
    output_file_png = output_file_base.with_suffix(".png")

    do_generate_audio = False
    tts_voice = "nova"
    if questionary.confirm("Generate MP3 audio file for course?").ask():
        tts_voice = questionary.select(
            "Choose a voice for the course lecturer", choices=TTS_VOICES, default=tts_voice
        ).ask()
        do_generate_audio = True
        if questionary.confirm("Generate cover image for audio file?").ask():
            generate_course_image(outline, output_file_png)

    print("Generating course text...")
    course = generate_course_lectures(outline)

    if do_generate_audio:
        print("Generating course audio...")
        course_audio_path = generate_course_audio(
            course, output_file_mp3, tts_voice, output_file_png if output_file_png.exists() else None
        )
        print(f"Course audio: {str(course_audio_path)}")

    # Writing JSON output synchronously
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file_json, "w", encoding="utf-8") as f:
        f.write(course.model_dump_json(indent=2))
    print(f"Course JSON:  {str(output_file_json)}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting.")
