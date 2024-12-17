# cli_example.py
import sys

import questionary

from okcourse import (
    get_duration_string_from_seconds,
    generate_course,
    generate_course_outline,
    generate_course_text,
    generate_course_audio,
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
            f"How many lectures should be in the series (default: {num_lectures_default})?"
        ).ask()

        if not num_lectures:
            num_lectures = num_lectures_default

        try:
            num_lectures = int(num_lectures)
            if num_lectures > 0:
                break
            else:
                print("Number of lectures must be greater than 0.")
        except ValueError:
            print("Enter a number greater than 0.")

    # outline = generate_course_outline(topic, num_lectures)
    # if not questionary.confirm(f"Continue generating lectures for this course outline?\n\n{str(outline)}").ask():
    #     print("Canceled - exiting.")
    #     exit(0)

    do_generate_audio = False
    if questionary.confirm("Generate MP3 audio file for course?").ask():
        do_generate_audio = True

    do_generate_cover_art = False
    if do_generate_audio:
        if questionary.confirm("Generate image for audio file album art?").ask():
            do_generate_cover_art = True

    print("Generating course...")
    results = generate_course(topic, num_lectures, do_generate_audio, do_generate_cover_art)

    print(f"Done! Series generated in {get_duration_string_from_seconds(results['total_seconds_elapsed'])}")
    print(f"  Text:  {results['course_text_path']}")
    if do_generate_audio:
        print(f"  Audio: {results['course_audio_path']}")
    if do_generate_cover_art:
        print(f"  Cover: {results['course_cover_path']}")


if __name__ == "__main__":
    main()
