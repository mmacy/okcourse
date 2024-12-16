# cli_example.py
import sys

import questionary

from okcourse import (
    get_duration_string_from_seconds,
    generate_complete_lecture_series,
    # generate_lecture_series_outline,
    # generate_text_for_lectures_in_series,
    # generate_audio_for_lectures_in_series,
)

num_lectures_default = 20


def main():
    print("=======================")
    print("==  OK Course Maker  ==")
    print("=======================")

    topic = questionary.text("Enter a lecture series topic:").ask()
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

    do_generate_audio = False
    if questionary.confirm("Generate MP3 audio file for lecture series?").ask():
        do_generate_audio = True

    do_generate_cover_art = False
    if do_generate_audio:
        if questionary.confirm("Generate image for audio file album art").ask():
            do_generate_cover_art = True

    print("Generating lecture series...")
    results = generate_complete_lecture_series(topic, num_lectures, do_generate_audio, do_generate_cover_art)

    print(f"Done! Series generated in {get_duration_string_from_seconds(results['total_seconds_elapsed'])}")
    print(f"  Text:  {results['series_text_path']}")
    if do_generate_audio:
        print(f"  Audio: {results['series_audio_path']}")
    if do_generate_cover_art:
        print(f"  Cover: {results['series_cover_path']}")


if __name__ == "__main__":
    main()
