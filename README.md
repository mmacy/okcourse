# okcourse

The `okcourse` Python library generates audiobook-style courses with lectures on any topic by using artificial intelligence (AI).

The async version of the `okcourse` OpenAI generator can produce a **1.5-hour** long audio course with 20 lectures on a topic of your choosing in around **2 minutes**.

## Prerequisites

- [Python 3.12+](https://python.org) or [uv](https://docs.astral.sh/uv/)[^1]
- [FFmpeg](https://ffmpeg.org/)
- [OpenAI API key](https://platform.openai.com/docs/quickstart)

[^1]: uv can [install the right Python version](https://docs.astral.sh/uv/guides/install-python/) for you.

## Install uv (optional)

Install Astral's [uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't already have it.

Though not strictly required, many people find working with Python projects *much* easier with `uv` than with other tools. In fact, `uv` will even [install Python](https://docs.astral.sh/uv/guides/install-python/) for you!

If you prefer, you *can* use `python -m venv` + `pip`, Poetry, or another tool you to create and manage your Python environment, but since this project uses `uv`, so will these instructions.

## Install `okcourse` package

To use the `okcourse` library in your Python project, install the package directly from GitHub (it's not yet on PyPi).

For example, to install it with [uv](https://docs.astral.sh/uv/), run the following command in your project directory:

```sh
# Install okcourse package from GitHub repo
uv add git+https://github.com/mmacy/okcourse.git
```

## Prepare to contribute

You might also like to try generating a course or two using an `okcourse` example app. Or maybe you'd like to contribute your awesome code or doc skills to the `okcourse` project. In either case, complete the following steps to prepare your environment.

1. Clone the repo with `git` and enter the project root:

    ```sh
    # Clone repo using SSH
    git clone git@github.com:mmacy/okcourse.git

    # Enter project root dir
    cd okcourse
    ```

1. Run the async CLI example app with `uv run`.

    By running the example app, `uv` will automatically create a virtual environment that includes the required version of Python and install the project dependencies.

    ```
    uv run examples/cli_example_async.py
    ```

You're welcome at this point to generate a course by answering the CLI's prompts. However, unless you already have your OpenAI API access token in an environment variable as described in the next section, *course generation will fail*.

## Enable AI API access

The `okcourse` library and example apps look for an environment variable containing an API token when creating the client to interact with the AI service provider's API.

As a friendly reminder, using `okcourse` to generate course content may cost you, your employer, or whomever owns the API token money for API usage.

!!! warning

    The API token owner is responsible for API usage fees incurred by using `okcourse`.

Set the environment variable appropriate for your AI service provider.

| AI provider  | Set this environment variable |
| :-------: | :---------------------------: |
|  OpenAI   |       `OPENAI_API_KEY`        |
| Anthropic |      *not yet supported*      |
|  Google   |      *not yet supported*      |

## Generate a course

To see the library in action, generate your first course by running the example CLI application with `uv` and answering the prompts:

```sh
uv run examples/cli_example_async.py
```

Output from generating a four-lecture course with `cli_example_async.py` and `INFO` logging enabled looks similar to the following:

```console
$ uv run examples/cli_example_async.py
=======================
==  OK Course Maker  ==
=======================
? Enter a course topic: Artificial Super Intelligence: Paperclips All The Way Down
? Generate course using default settings? No
? How many lectures should be in the course? 4
? Generate MP3 audio file for course? Yes
? Choose a voice for the course lecturer nova
? Generate cover image for audio file? Yes
? Enter a directory for the course output: /Users/mmacy/.okcourse_files
Generating course outline with 4 lectures...
2024-12-29 13:39:21 [INFO][okcourse.generators.openai.async_openai] Requesting outline for course 'Artificial Super Intelligence: Paperclips All The Way Down'...
Course title: Artificial Super Intelligence: Paperclips All The Way Down

Lecture 1: Introduction to Artificial Superintelligence
  - Definition and Characteristics of Artificial Superintelligence
  - Historical Context and Evolution of AI Capabilities
  - Potential Trajectories and Timelines for ASI Development
  - Ethical Considerations and Philosophical Implications

Lecture 2: The Paperclip Maximizer Thought Experiment
  - Origin and Explanation of the Paperclip Maximizer Scenario
  - Implications for Goal Alignment in Autonomous Systems
  - The Role of Utility Functions and Instrumental Convergence
  - Critiques and Counterarguments to the Paperclip Scenario

Lecture 3: Technical Challenges in Building ASI
  - Scalable Machine Learning and Computational Requirements
  - Self-improvement and Recursive Self-enhancement
  - Robust Decision-Making and Intelligence Amplification
  - Challenges in Interpretability and Transparency

Lecture 4: Control and Safety Mechanisms
  - Specification Gaming and Misalignment Risks
  - Value Alignment and Cooperative Inverse Reinforcement Learning
  - Corrigibility and Interruptibility in AI Systems
  - Research Agendas for Safe and Beneficial ASI


? Proceed with this outline? Yes
Generating content for 4 course lectures...
2024-12-29 13:39:35 [INFO][okcourse.generators.openai.async_openai] Requesting lecture text for topic 1/4: Introduction to Artificial Superintelligence...
2024-12-29 13:39:35 [INFO][okcourse.generators.openai.async_openai] Requesting lecture text for topic 2/4: The Paperclip Maximizer Thought Experiment...
2024-12-29 13:39:35 [INFO][okcourse.generators.openai.async_openai] Requesting lecture text for topic 3/4: Technical Challenges in Building ASI...
2024-12-29 13:39:35 [INFO][okcourse.generators.openai.async_openai] Requesting lecture text for topic 4/4: Control and Safety Mechanisms...
2024-12-29 13:39:39 [INFO][okcourse.generators.openai.async_openai] Got lecture text for topic 3/4 @ 3146 chars: Technical Challenges in Building ASI.
2024-12-29 13:39:40 [INFO][okcourse.generators.openai.async_openai] Got lecture text for topic 4/4 @ 4264 chars: Control and Safety Mechanisms.
2024-12-29 13:39:41 [INFO][okcourse.generators.openai.async_openai] Got lecture text for topic 1/4 @ 4314 chars: Introduction to Artificial Superintelligence.
2024-12-29 13:39:42 [INFO][okcourse.generators.openai.async_openai] Got lecture text for topic 2/4 @ 5103 chars: The Paperclip Maximizer Thought Experiment.
Generating cover image...
2024-12-29 13:39:52 [INFO][okcourse.generators.openai.async_openai] Saving image to /Users/mmacy/.okcourse_files/artificial_super_intelligence_paperclips_all_the_way_down.png
Generating course audio...
2024-12-29 13:39:52 [INFO][okcourse.utils] Checking for NLTK 'punkt_tab' tokenizer...
2024-12-29 13:39:52 [INFO][okcourse.utils] Found NLTK 'punkt_tab' tokenizer.
2024-12-29 13:39:52 [INFO][okcourse.utils] Split text into 5 chunks of ~4096 characters from 103 sentences.
2024-12-29 13:39:52 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 1...
2024-12-29 13:39:52 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 2...
2024-12-29 13:39:52 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 3...
2024-12-29 13:39:52 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 4...
2024-12-29 13:39:52 [INFO][okcourse.generators.openai.async_openai] Requesting TTS audio in voice 'nova' for text chunk 5...
2024-12-29 13:40:00 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 5 in voice 'nova'.
2024-12-29 13:40:17 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 2 in voice 'nova'.
2024-12-29 13:40:19 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 4 in voice 'nova'.
2024-12-29 13:40:19 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 3 in voice 'nova'.
2024-12-29 13:40:26 [INFO][okcourse.generators.openai.async_openai] Got TTS audio for text chunk 1 in voice 'nova'.
2024-12-29 13:40:26 [INFO][okcourse.generators.openai.async_openai] Joining 5 audio chunks into one file...
2024-12-29 13:40:26 [INFO][okcourse.generators.openai.async_openai] Exporting audio file...
Done! Course file(s) saved to /Users/mmacy/.okcourse_files
```

*BEHOLD!* A four-lecture audio course about ASI by AI, complete with AI-generated album art.

I'm guessing the two `I`s in "SERIIES" is for a double dose of intelligence.

![Screenshot Apple's Music app interface showing album 'OK Courses' by Nova @ OpenAI, categorized as Books & Spoken from 2024. The cover art features a stylized illustration of technology components, paperclips, and a robotic hand. The selected track, 'Artificial Super Intelligence: Paperclips All The Way Down,' is 17 minutes and 42 seconds long.](images/media-player-01.png)
