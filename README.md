# okcourse

The `okcourse` Python library creates audiobook-style courses with lectures on any topic by using text completion, text-to-speech, and image AI models to generate course content.

![Screenshot of Apple's Music app interface showing album 'OK Courses' by Nova & o1-preview-2024-09-12 @ OpenAI, categorized as Books & Spoken from 2025. The cover art features a stylized illustration of a Commodore 64 and components and misspelled words resembling the selected track's name, 'Commodore 64 Assembly Programming with KickAssembler and VICE,' which is 3 hours, 14 minutes, and 51 seconds long.][media-player-01]

## Prerequisites

- [Python 3.12+](https://python.org)
- [OpenAI API key](https://platform.openai.com/docs/quickstart) set in `OPENAI_API_KEY` environment variable

## Installation

### Install from PyPi

Use `pip`, `uv`, Poetry, or another package manager to install the `okcourse` package from PyPi.

For example, to  install the package with `pip`:

```sh
# Install okcourse package from PyPi (recommended)
pip install okcourse
```

### Install from GitHub

I recommend installing from PyPi as described above. You can, however, install the latest (possibly busted) version of the library directly from the `main` branch of the GitHub repo by using [uv](https://docs.astral.sh/uv/):

```sh
# Install okcourse directly from GitHub
uv add git+https://github.com/mmacy/okcourse.git # (1)!
```

1. Installing directly from the tip of a GitHub repo's default branch is like installing a nightly dev build and can also be considered risky from a security standpoint—[caveat emptor](https://www.findlaw.com/consumer/consumer-transactions/what-does-caveat-emptor-mean-.html).

## Generate a course

A complete "course" has five components: title, outline, lectures, cover art, and audio file.

To generate an outline, you provide a title. Once you've generated the outline, you can generate the lectures, cover art, and audio.

```mermaid
graph LR
    A[Title] --> B[Outline]
    B --> C[Lectures]
    C --> D[Cover]
    D --> E[Audio]
```

At a minimum, import [`Course`][okcourse.Course] and a generator, like [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator], and you can start generating courses.

```python
import asyncio
from okcourse import Course, OpenAIAsyncGenerator

async def main() -> None:
    """Use the OpenAIAsyncGenerator to generate a complete course."""

    # Create a course, configure its settings, and initialize the generator
    course = Course(title="From AGI to ASI: Paperclips, Gray Goo, and You")
    generator = OpenAIAsyncGenerator(course)

    # Generate all course content - these call the AI model provider's API
    course = await generator.generate_outline(course)
    course = await generator.generate_lectures(course)
    course = await generator.generate_image(course)
    course = await generator.generate_audio(course)

    # The course should now be populated with an outline, lectures, and
    # links to its cover image (PNG) and audio (MP3) files.

    # The 'Course' object is a Pydantic model, as are its nested models,
    # so they support (de)serialization out of the box. For example, you
    # can print the course in JSON format to the console with Pydantic's
    # BaseModel.model_dump_json() method:
    print(course.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

The previous code snippet demonstrates generating a course from only a title, but there are several other settings available for tuning course generation.

[`CourseSettings`][okcourse.CourseSettings] lets you configure the number of lectures, number of subtopics in each lecture, and which AI models to use for generating the course content (lecture text, cover image, and audio file).

## Run an example app

To see the library in action, try generating a course by running an [example app](/okcourse/examples/).

For example, if you've installed [uv](https://docs.astral.sh/uv/), run the CLI script with `uv run`:

```sh
uv run examples/cli_example_async.py
```

Output from a successful course generation with `cli_example_async.py` and default settings looks similar to the following:

```console
$ uv run examples/cli_example_async.py
Reading inline script metadata from `examples/cli_example_async.py`
 Updated https://github.com/mmacy/okcourse (c185da3)
============================
==  okcourse CLI (async)  ==
============================
? Enter a course topic: Artificial Super Intelligence: Paperclips All The Way Down
? How many lectures should be in the course? 4
? Generate MP3 audio file for course? Yes
? Choose a voice for the course lecturer nova
? Generate cover image for audio file? Yes
? Enter a directory for the course output: /Users/mmacy/.okcourse_files
Generating course outline with 4 lectures...
2025-01-01 12:27:36 [INFO][okcourse.generators.openai.async_openai] Requesting outline for course 'Artificial Super Intelligence: Paperclips All The Way Down'...
Course title: Artificial Super Intelligence: Paperclips All The Way Down

Lecture 1: Foundations of Artificial Super Intelligence
  - Definition and Characteristics of Super Intelligence
  - Theoretical Frameworks of ASI
  - Historical Context and Development
  - Ethical and Philosophical Considerations

Lecture 2: Development Pathways and Approaches
  - Machine Learning and AI Scaling Laws
  - Neural Networks and AGI
  - Emergent Behavior in Complex Systems
  - Simulation Theory and ASI

Lecture 3: Risks and Containment Strategies
  - Existential Risks and Global Impact
  - Control Problem and Alignment Challenges
  - Supervision and Containment Protocols
  - Scenario Analysis and Risk Assessment

Lecture 4: The Paperclip Maximizer Thought Experiment
  - Overview and Implications of the Thought Experiment
  - Unintended Consequences and Path Dependency
  - Utility Functions and Value Alignment
  - Mitigation Strategies and Ethical Considerations


? Proceed with this outline? Yes
Generating content for 4 course lectures...
2025-01-01 12:28:03 [INFO][okcourse.generators.openai.async_openai] Requesting lecture text for topic 1/4: Foundations of Artificial Super Intelligence...
2025-01-01 12:28:03 [INFO][okcourse.generators.openai.async_openai] Requesting lecture text for topic 2/4: Development Pathways and Approaches...
2025-01-01 12:28:03 [INFO][okcourse.generators.openai.async_openai] Requesting lecture text for topic 3/4: Risks and Containment Strategies...
2025-01-01 12:28:03 [INFO][okcourse.generators.openai.async_openai] Requesting lecture text for topic 4/4: The Paperclip Maximizer Thought Experiment...
2025-01-01 12:28:08 [INFO][okcourse.generators.openai.async_openai] Got lecture text for topic 1/4 @ 4093 chars: Foundations of Artificial Super Intelligence.
2025-01-01 12:28:09 [INFO][okcourse.generators.openai.async_openai] Got lecture text for topic 2/4 @ 4125 chars: Development Pathways and Approaches.
2025-01-01 12:28:09 [INFO][okcourse.generators.openai.async_openai] Got lecture text for topic 4/4 @ 5140 chars: The Paperclip Maximizer Thought Experiment.
2025-01-01 12:28:10 [INFO][okcourse.generators.openai.async_openai] Got lecture text for topic 3/4 @ 5133 chars: Risks and Containment Strategies.
Generating cover image...
2025-01-01 12:28:23 [INFO][okcourse.generators.openai.async_openai] Saving image to /Users/mmacy/.okcourse_files/artificial_super_intelligence_paperclips_all_the_way_down.png
Generating course audio...
2025-01-01 12:28:23 [INFO][okcourse.utils] Checking for NLTK 'punkt_tab' tokenizer...
2025-01-01 12:28:23 [INFO][okcourse.utils] Found NLTK 'punkt_tab' tokenizer.
2025-01-01 12:28:23 [INFO][okcourse.utils] Split text into 5 chunks of ~4096 characters from 113 sentences.
2025-01-01 12:28:23 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 1...
2025-01-01 12:28:23 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 2...
2025-01-01 12:28:23 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 3...
2025-01-01 12:28:23 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 4...
2025-01-01 12:28:23 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 5...
2025-01-01 12:28:44 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 5 in voice 'nova'.
2025-01-01 12:28:51 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 2 in voice 'nova'.
2025-01-01 12:28:51 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 4 in voice 'nova'.
2025-01-01 12:28:53 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 1 in voice 'nova'.
2025-01-01 12:28:53 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 3 in voice 'nova'.
2025-01-01 12:28:53 [INFO][okcourse.generators.openai.async_openai] Joining 5 audio chunks into one file...
2025-01-01 12:28:53 [INFO][okcourse.generators.openai.async_openai] Saving audio to /Users/mmacy/.okcourse_files/artificial_super_intelligence_paperclips_all_the_way_down.mp3
Course JSON file saved to /Users/mmacy/.okcourse_files/artificial_super_intelligence_paperclips_all_the_way_down.json
Done! Course file(s) available in /Users/mmacy/.okcourse_files
```

*BEHOLD!* A four-lecture audio course about Artificial Super Intelligence by Artificial Not-So-Super Intelligence, with AI-generated album art complete with misspellings (the two **I**s in *SERIIES* are for a double dose of intelligence, I'm guessing):

![Screenshot of Apple's Music app interface showing album 'OK Courses' by Nova @ OpenAI, categorized as Books & Spoken from 2024. The cover art features a stylized illustration of technology components, paperclips, and a robotic hand. The selected track, 'Artificial Super Intelligence: Paperclips All The Way Down,' is 17 minutes and 42 seconds long.][media-player-02]

[media-player-01]: https://raw.githubusercontent.com/mmacy/okcourse/1467e9366bd996fc6fa76cac941226d56f2a4796/images/media-player-01.png
[media-player-02]: https://raw.githubusercontent.com/mmacy/okcourse/1467e9366bd996fc6fa76cac941226d56f2a4796/images/media-player-02.png
