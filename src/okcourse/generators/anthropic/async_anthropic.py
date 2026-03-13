"""The `async_anthropic` module contains the [`AnthropicAsyncGenerator`][okcourse.AnthropicAsyncGenerator] class.

Requires the `ANTHROPIC_API_KEY` environment variable.
"""

import asyncio
import random
from string import Template
from typing import Any, Awaitable, Callable, TypeVar

from anthropic import AsyncAnthropic, RateLimitError

from okcourse.constants import MAX_LECTURES
from okcourse.generators.base import CourseGenerator
from okcourse.models import Course, CourseLecture, CourseOutline, CourseSettings
from okcourse.utils.log_utils import get_logger, time_tracker
from okcourse.utils.text_utils import LLM_SMELLS, swap_words


_log = get_logger(__name__)

_ANTHROPIC_DEFAULT_TEXT_MODEL = "claude-sonnet-4-6"
_SETTINGS_DEFAULTS = CourseSettings()

T = TypeVar("T")


def _get_retry_after_ms(error: RateLimitError) -> float | None:
    """Extracts the retry-after wait time in milliseconds from a RateLimitError's response headers.

    Checks `retry-after-ms` first (millisecond precision), then falls back to `Retry-After` (seconds).

    Args:
        error: The rate-limit exception containing response headers.

    Returns:
        Wait time in milliseconds, or `None` if unavailable.
    """
    try:
        headers = error.response.headers
        retry_after_ms = headers.get("retry-after-ms")
        if retry_after_ms:
            return float(retry_after_ms)
        retry_after = headers.get("retry-after")
        if retry_after:
            return float(retry_after) * 1000
    except (AttributeError, ValueError, TypeError):
        pass
    return None


async def _execute_with_retry(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 6,
    initial_delay_ms: float = 1000,
    **kwargs: Any,
) -> T:
    """Calls an async function and retries with exponential backoff on RateLimitError.

    Args:
        func: The async function to call.
        *args: Positional arguments to pass to the function.
        max_retries: Maximum number of retries before giving up.
        initial_delay_ms: Initial delay in milliseconds before the first retry.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The awaited result of `func`.

    Raises:
        Exception: If `max_retries` is exceeded.
    """
    attempt = 0
    delay_ms = initial_delay_ms

    while True:
        try:
            return await func(*args, **kwargs)
        except RateLimitError as rle:
            _log.warning(f"RateLimitError hit: {rle}")
            attempt += 1
            if attempt > max_retries:
                raise Exception(f"Max retries ({max_retries}) exceeded.") from rle

            retry_after_ms = _get_retry_after_ms(rle)
            if retry_after_ms:
                delay_ms = max(delay_ms, retry_after_ms)
            delay_ms *= 2 * (1 + random.random())

            _log.warning(f"Will retry in {round(delay_ms / 1000, 2)} seconds (attempt {attempt}/{max_retries})...")
            await asyncio.sleep(delay_ms / 1000)


class AnthropicAsyncGenerator(CourseGenerator):
    """Uses the Anthropic API to generate course outlines and lecture text asynchronously.

    This generator supports text generation (outline and lectures) using Claude models.
    Image and audio generation are not available through the Anthropic API and will raise
    `NotImplementedError` if called.

    If `course.settings.text_model_outline` or `text_model_lecture` are set to OpenAI
    model IDs, they are automatically replaced with `claude-sonnet-4-6`.

    Requires the `ANTHROPIC_API_KEY` environment variable.

    Examples:

    ```python
    import asyncio
    from okcourse import Course
    from okcourse import AnthropicAsyncGenerator

    async def main():
        course = Course(title="Foundations of Distributed Systems")
        generator = AnthropicAsyncGenerator(course)
        course = await generator.generate_outline(course)
        course = await generator.generate_lectures(course)

    asyncio.run(main())
    ```
    """

    def __init__(self, course: Course):
        """Initializes the asynchronous Anthropic course generator.

        Args:
            course: The course to generate content for.
        """
        # If the user left text models at their default values, replace with Claude defaults
        if course.settings.text_model_outline == _SETTINGS_DEFAULTS.text_model_outline:
            course.settings.text_model_outline = _ANTHROPIC_DEFAULT_TEXT_MODEL
        if course.settings.text_model_lecture == _SETTINGS_DEFAULTS.text_model_lecture:
            course.settings.text_model_lecture = _ANTHROPIC_DEFAULT_TEXT_MODEL

        super().__init__(course)
        self.client = AsyncAnthropic()

    async def generate_outline(self, course: Course) -> Course:
        """Generates a course outline based on its `title` and other [`settings`][okcourse.models.Course.settings].

        Set the course's [`title`][okcourse.models.Course.title] attribute before calling this method.

        Args:
            course: The course to generate an outline for. Must have its `title` attribute set.

        Returns:
            Course: The result of the generation process with its `course.outline` attribute set.

        Raises:
            ValueError: If the course has no title, the lecture count exceeds the maximum, or
                the model returns no structured output.
        """
        if not course.title or course.title.strip() == "":
            msg = "The given Course has no title. Set the course's 'title' attribute before calling this method."
            self.log.error(msg)
            raise ValueError(msg)
        if course.settings.num_lectures > MAX_LECTURES:
            msg = f"Number of lectures exceeds the maximum allowed ({MAX_LECTURES})."
            self.log.error(msg)
            raise ValueError(msg)

        course.settings.output_directory = course.settings.output_directory.expanduser().resolve()

        outline_prompt = Template(course.settings.prompts.outline).substitute(
            num_lectures=course.settings.num_lectures,
            course_title=course.title,
            num_subtopics=course.settings.num_subtopics,
        )

        self.log.info(f"Requesting outline for course '{course.title}'...")
        with time_tracker(course.generation_info, "outline_gen_elapsed_seconds"):
            response = await _execute_with_retry(
                self.client.messages.parse,
                model=course.settings.text_model_outline,
                max_tokens=4096,
                system=course.settings.prompts.system,
                messages=[{"role": "user", "content": outline_prompt}],
                output_format=CourseOutline,
            )
        self.log.info(f"Received outline for course '{course.title}'.")

        if response.usage:
            course.generation_info.outline_input_token_count += response.usage.input_tokens
            course.generation_info.outline_output_token_count += response.usage.output_tokens

        generated_outline = response.parsed_output
        if generated_outline is None:
            msg = "Model returned no structured output for the course outline."
            self.log.error(msg)
            raise ValueError(msg)

        if generated_outline.title.lower() != course.title.lower():
            self.log.info(f"Resetting course topic to '{course.title}' (LLM returned '{generated_outline.title}')")
            generated_outline.title = course.title

        course.outline = generated_outline
        return course

    async def _generate_lecture(self, course: Course, lecture_number: int) -> CourseLecture:
        """Generates a lecture for the topic with the specified number in the given outline.

        Args:
            course: The course with a populated `outline` attribute.
            lecture_number: The position number of the lecture to generate.

        Returns:
            A `CourseLecture` object for the given lecture number.

        Raises:
            ValueError: If no topic is found for the given lecture number or the model returns no text.
        """
        if course.outline is None:
            raise ValueError("Course has no outline. Call generate_outline() first.")
        topic = next((t for t in course.outline.topics if t.number == lecture_number), None)
        if not topic:
            raise ValueError(f"No topic found for lecture number {lecture_number}")

        lecture_prompt = Template(course.settings.prompts.lecture).substitute(
            lecture_title=topic.title,
            course_title=course.title,
            course_outline=str(course.outline),
        )

        self.log.info(
            f"Requesting lecture text for topic {topic.number}/{len(course.outline.topics)}: {topic.title}..."
        )

        response = await _execute_with_retry(
            self.client.messages.create,
            model=course.settings.text_model_lecture,
            max_tokens=16000,
            system=course.settings.prompts.system,
            messages=[{"role": "user", "content": lecture_prompt}],
        )

        if response.usage:
            course.generation_info.lecture_input_token_count += response.usage.input_tokens
            course.generation_info.lecture_output_token_count += response.usage.output_tokens

        text_block = next((b for b in response.content if b.type == "text"), None)
        if text_block is None:
            raise ValueError(f"Model returned no text content for lecture {lecture_number}: {topic.title}")
        lecture_text = swap_words(text_block.text.strip(), LLM_SMELLS)

        self.log.info(
            f"Got lecture text for topic {topic.number}/{len(course.outline.topics)} "
            f"@ {len(lecture_text)} chars: {topic.title}."
        )
        return CourseLecture(**topic.model_dump(), text=lecture_text)

    async def generate_lectures(self, course: Course) -> Course:
        """Generates the text for the lectures in the course outline.

        Returns:
            The `Course` with its `course.lectures` attribute set to all successfully generated lectures.
        """
        course.settings.output_directory = course.settings.output_directory.expanduser().resolve()
        if course.outline is None:
            raise ValueError("Course has no outline. Call generate_outline() first.")
        lecture_tasks: list[asyncio.Task[CourseLecture]] = []

        with time_tracker(course.generation_info, "lecture_gen_elapsed_seconds"):
            try:
                async with asyncio.TaskGroup() as task_group:
                    for topic in course.outline.topics:
                        task = task_group.create_task(
                            self._generate_lecture(course, topic.number),
                            name=f"generate_lecture_{topic.number}",
                        )
                        lecture_tasks.append(task)
            except ExceptionGroup as eg:
                for e in eg.exceptions:
                    self.log.error(f"Error generating lecture: {e}")

        course.lectures = [
            t.result() for t in lecture_tasks if not t.cancelled() and t.exception() is None
        ]
        return course

    async def generate_image(self, course: Course) -> Course:  # noqa: ARG002
        """Not supported by the Anthropic API.

        Raises:
            NotImplementedError: Always. Use
                [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator] for image generation.
        """
        raise NotImplementedError(
            "Image generation is not supported by the Anthropic API. "
            "Use OpenAIAsyncGenerator for image generation."
        )

    async def generate_audio(self, course: Course) -> Course:  # noqa: ARG002
        """Not supported by the Anthropic API.

        Raises:
            NotImplementedError: Always. Use
                [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator] for audio generation.
        """
        raise NotImplementedError(
            "Audio generation is not supported by the Anthropic API. "
            "Use OpenAIAsyncGenerator for audio generation."
        )
