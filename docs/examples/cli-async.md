# CLI - async, interactive

The [`cli_example_async.py`](https://github.com/mmacy/okcourse/blob/main/examples/cli_example_async.py) script is an interactive CLI that uses the [`OpenAIAsyncGenerator`][okcourse.generators.OpenAIAsyncGenerator] to generate courses.

You can run this script directly from GitHub with [uv](https://docs.astral.sh/uv/guides/scripts/):

```sh
uv run --no-cache https://raw.githubusercontent.com/mmacy/okcourse/refs/heads/main/examples/cli_example_async.py
```

Using [Questionary](https://questionary.readthedocs.io/), the script prompts the user for a course title and then generates an outline they can accept or reject. Once the user accepts an outline, they're asked whether to generate course audio and a cover image. Finally, the `OpenAIAsyncGenerator` generates the lecture text based on the outline and (if specified) an MP3 with generated album art.

```python title="cli_example_async.py"
--8<-- "examples/cli_example_async.py"
```
