# okcourse

The `okcourse` Python library generates audiobook-style courses with lectures on any topic by using artificial intelligence (AI).

The async version of the `okcourse` OpenAI generator can produce a **1.5-hour** long audio course with 20 lectures on a topic of your choosing in around **2 minutes**.

## Prerequisites

- [Python 3.12+](https://python.org)
- [OpenAI API key](https://platform.openai.com/docs/quickstart)

## Install uv (optional)

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) by Astral if you don't already have it.

Though not strictly required, many people find working with Python projects *much* easier with `uv` than with other tools. In fact, `uv` will even [install Python](https://docs.astral.sh/uv/guides/install-python/) for you!

If you prefer, you *can* use `python -m venv`, Poetry, or another tool to create and manage your Python environment, but since this project uses `uv`, so will these instructions.

## Install `okcourse` package

To use the `okcourse` library in your Python project, install the package directly from GitHub (it's not yet on PyPi).

For example, to install it with [uv](https://docs.astral.sh/uv/), run the following command in your project directory:

```sh
# Install okcourse package from GitHub repo
uv add git+https://github.com/mmacy/okcourse.git
```

## Prepare to contribute

If you'd like to contribute your awesome code or doc skills to the `okcourse` project or try out an example app, complete the following steps to prepare your environment.

1. Clone the repo with `git` and enter the project root:

    ```sh
    # Clone repo using SSH
    git clone git@github.com:mmacy/okcourse.git

    # Enter project root dir
    cd okcourse
    ```

2. Run the async CLI example app with `uv run`.

    By running the example app, `uv` will automatically create a virtual environment that includes the required Python version and install the project dependencies.

    ```
    uv run examples/cli_example_async.py
    ```

If your OpenAI API key is already available in an environment variable, you can generate your first course now by answering the prompts in the CLI.

If your OpenAI API is *not* available, however, move on to the next section.

## Enable AI API access

The `okcourse` library and example apps look for an environment variable containing an API key when creating the client to interact with the AI service provider's API.

As a friendly reminder, using `okcourse` to generate course content may cost you, your employer, or whomever owns the API key money for API usage.

!!! warning

    The API token owner is responsible for API usage fees incurred by using `okcourse`.

Set the environment variable appropriate for your AI service provider.

| AI provider | Set this environment variable |
| :---------: | :---------------------------: |
|   OpenAI    |       `OPENAI_API_KEY`        |
|  Anthropic  |      *not yet supported*      |
|   Google    |      *not yet supported*      |

## Generate a course

To see the library in action, generate your first course by running the example CLI application with `uv` and answering the prompts:

```sh
uv run examples/cli_example_async.py
```

Output from running `cli_example_async.py` using the default  `4` lectures and `INFO` logging level looks similar to the following:

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

*BEHOLD!* A four-lecture audio course about ASI by AI, complete with AI-generated album art.

I'm guessing the two `I`s in "SERIIES" is for a double dose of intelligence.

![Screenshot Apple's Music app interface showing album 'OK Courses' by Nova @ OpenAI, categorized as Books & Spoken from 2024. The cover art features a stylized illustration of technology components, paperclips, and a robotic hand. The selected track, 'Artificial Super Intelligence: Paperclips All The Way Down,' is 17 minutes and 42 seconds long.](images/media-player-01.png)
