# cli_example.py
import os
import sys
from pathlib import Path

import questionary

from okcourse import (
    get_duration_string_from_seconds,
    generate_course,
    generate_course_outline,
    generate_course_lectures,
    generate_course_audio,
    sanitize_filename,
    TTS_VOICES,
)

num_lectures_default = 20


def main():
    print("=======================")
    print("==  OK Course Maker  ==")
    print("=======================")

    topic = questionary.text("Enter a course topic:").ask()
    if not topic:
        print("No topic entered - exiting.")
        sys.exit(0)

    while True:
        num_lectures = questionary.text(
            f"How many lectures should be in the course (default: {num_lectures_default})?"
        ).ask()

        if not num_lectures:
            num_lectures = num_lectures_default

        try:
            num_lectures = int(num_lectures)
            if num_lectures > 0:
                break
            else:
                print("There must be at least one (1) lecture in the series.")
        except ValueError:
            print("Enter a number greater than 0.")

    while True:
        print(f"Generating course outline with {num_lectures} lectures...")
        outline = generate_course_outline(topic, num_lectures)
        print(os.linesep)
        print(str(outline))
        print(os.linesep)

        if questionary.confirm("Proceed with this outline?").ask():
            break

        if not questionary.confirm("Generate a new outline?").ask():
            print("Cannot generate lecture without outline - exiting.")
            exit(0)

    do_generate_audio = False
    tts_voice = "nova"
    if questionary.confirm("Generate MP3 audio file for course?").ask():
        tts_voice = questionary.select(
            "Choose a voice for the course lecturer",
            choices=TTS_VOICES,
            default=tts_voice
        ).ask()
        do_generate_audio = True

    do_generate_cover_art = False
    if do_generate_audio:
        if questionary.confirm("Generate cover image for audio file?").ask():
            do_generate_cover_art = True

    print("Generating course text...")
    course = generate_course_lectures(outline)

    output_dir = Path.cwd() / "generated_okcourses"
    output_file_base = output_dir / sanitize_filename(course.title)
    output_file_mp3 = output_file_base.with_suffix(".mp3")
    output_file_json = output_file_base.with_suffix(".json")

    if do_generate_audio:
        print("Generating course audio...")
        course_audio_path = generate_course_audio(course, str(output_file_mp3), tts_voice, do_generate_cover_art)
        print(f"Course audio: {str(course_audio_path)}")

    output_file_json.write_text(course.model_dump_json(indent=2))
    print(f"Course JSON:  {str(output_file_json)}")

if __name__ == "__main__":
    main()
