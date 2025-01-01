# Example apps

## CLI async

This script uses the [`OpenAIAsyncGenerator`][okcourse.generators.OpenAIAsyncGenerator] to generate OK courses.

It uses [Questionary](https://questionary.readthedocs.io/) to prompt the user for a course title, then generates an outline, allowing the user to regenerate it until they're satisfied. Assuming the user accepts an outline, the `OpenAIAsyncGenerator` generates the lecture text and an also a cover image and audio (if desired).

```python
--8<-- "examples/cli_example_async.py"
```
