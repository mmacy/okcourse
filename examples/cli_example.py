# cli_app.py
import sys
import questionary
from okcourse import NUM_LECTURES, run_generation, format_time


def main():
    print("===================")
    print("==  Courserator  ==")
    print("===================")

    topic = questionary.text("Enter a lecture series topic:").ask()
    if not topic:
        print("No topic entered - exiting.")
        sys.exit(0)

    while True:
        num_lectures = questionary.text(f"How many lectures should be in the series (default: {NUM_LECTURES})?").ask()

        if not num_lectures:
            num_lectures = NUM_LECTURES

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

    print("Generating lecture series...")
    results = run_generation(topic, num_lectures, do_generate_audio)

    print("Lecture series generation complete.")
    print(f"Lecture series text: {results['series_text_path']}")
    if do_generate_audio:
        print(f"Lecture series audio: {results['audio_path']}")
    print(f"Total generation time: {format_time(results['total_time'])}")


if __name__ == "__main__":
    main()
