"""The `async_openai` module contains the [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator] class."""

import asyncio
import base64
import io
import random
import re
import time
from pathlib import Path
from string import Template
from typing import Any, Awaitable, Callable, TypeVar

from openai import APIError, APIStatusError, AsyncOpenAI, OpenAIError, RateLimitError

from okcourse.constants import AI_DISCLOSURE, MAX_LECTURES
from okcourse.generators.base import CourseGenerator
from okcourse.models import Course, CourseLecture, CourseOutline
from okcourse.utils.audio_utils import combine_mp3_buffers
from okcourse.utils.log_utils import get_top_level_version, time_tracker
from okcourse.utils.text_utils import (
    LLM_SMELLS,
    download_tokenizer,
    sanitize_filename,
    split_text_into_chunks,
    swap_words,
    tokenizer_available,
)

T = TypeVar("T")


def _parse_openai_rate_limit_wait_time(error_message: str) -> int:
    """Parses the OpenAI rate limit error message to extract wait time in seconds.

    If no specific wait time is found, returns a default of 60 seconds.

    Args:
        error_message: The error message returned by OpenAI containing rate limit info.

    Returns:
        The number of seconds to wait before retrying, or 60 if no time can be parsed.
    """
    match_minutes_seconds = re.search(r"Please try again in (\d+)m(\d+)s", error_message)
    if match_minutes_seconds:
        minutes, seconds = match_minutes_seconds.groups()
        return int(minutes) * 60 + int(seconds)

    match_seconds = re.search(r"Please try again in (\d+)s", error_message)
    if match_seconds:
        return int(match_seconds.group(1))

    return 60


async def _retry_with_exponential_backoff(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 6,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    logger: Any = None,
    **kwargs: Any,
) -> T:
    """Calls an async function and retries with exponential backoff on RateLimitError.

    This method parses the rate-limit-specific wait time from the OpenAI error message
    and uses random exponential backoff to avoid hammering the API in tight loops.

    Args:
        func: The function to call.
        *args: Positional arguments to pass to the function.
        max_retries: The maximum number of retries before giving up.
        initial_delay: The initial delay in seconds before the first retry.
        exponential_base: The exponential growth factor for delay intervals.
        jitter: Whether to apply random jitter to the delay interval.
        logger: A logger instance for logging retries and warnings.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The awaited result of `func`.

    Raises:
        Exception: If `max_retries` is exceeded.
    """
    attempt = 0
    delay = initial_delay

    while True:
        try:
            return await func(*args, **kwargs)
        except RateLimitError as exc:
            if logger:
                logger.warning(f"RateLimitError encountered: {exc}")

            attempt += 1
            if attempt > max_retries:
                raise Exception(f"Maximum number of retries ({max_retries}) exceeded.") from exc

            # Parse recommended wait time from the error, fall back to existing delay if smaller
            recommended_wait = _parse_openai_rate_limit_wait_time(str(exc))
            delay = max(delay, recommended_wait)

            # Add exponential backoff
            if jitter:
                # Multiply delay by random factor in [1, 2) to spread out bursts
                delay *= exponential_base * (1 + random.random())
            else:
                delay *= exponential_base

            if logger:
                logger.warning(f"Retrying in {round(delay, 2)} seconds (attempt {attempt}/{max_retries})...")
            await asyncio.sleep(delay)


class OpenAIAsyncGenerator(CourseGenerator):
    """Uses the OpenAI API to generate course content asynchronously.

    This class includes exponential backoff with optional random jitter when encountering
    rate limit errors from OpenAI.

    Examples:
    Generate a full course, including its outline, lectures, cover image, and audio file:

    ```python
    --8<-- "examples/snippets/async_openai_snippets.py:full_openaiasyncgenerator"
    ```
    """

    def __init__(self, course: Course):
        """Initializes the asynchronous OpenAI course generator.

        Args:
            course: The course to generate content for.
        """
        super().__init__(course)

        self.client = AsyncOpenAI()

    async def generate_outline(self, course: Course) -> Course:
        """Generates a course outline based on its `title` and other [`settings`][okcourse.models.Course.settings].

        Set the course's [`title`][okcourse.models.Course.title] attribute before calling this method.

        Returns:
            Course: The result of the generation process with its `course.outline` attribute set.

        Raises:
            ValueError: If the course has no title.

        Examples:
        ```python
        --8<-- "examples/snippets/async_openai_snippets.py:generate_outline"
        ```

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
            outline_completion = await _retry_with_exponential_backoff(
                self.client.beta.chat.completions.parse,
                model=course.settings.text_model_outline,
                messages=[
                    {"role": "system", "content": course.settings.prompts.system},
                    {"role": "user", "content": outline_prompt},
                ],
                response_format=CourseOutline,
                logger=self.log,
            )
        self.log.info(f"Received outline for course '{course.title}'...")

        if outline_completion.usage:
            course.generation_info.outline_input_token_count += outline_completion.usage.prompt_tokens
            course.generation_info.outline_output_token_count += outline_completion.usage.completion_tokens

        generated_outline = outline_completion.choices[0].message.parsed
        if generated_outline.title.lower() != course.title.lower():
            self.log.info(f"Resetting course topic to '{course.title}' (LLM returned '{generated_outline.title}'")
            generated_outline.title = course.title

        course.outline = generated_outline
        return course

    async def _generate_lecture(self, course: Course, lecture_number: int) -> CourseLecture:
        """Generates a lecture for the topic with the specified number in the given outline.

        Args:
            course: The course with a populated `outline` attribute containing lecture topics and their subtopics.
            lecture_number: The position number of the lecture to generate.

        Returns:
            A Lecture object representing the lecture for the given number.

        Raises:
            ValueError: If no topic is found for the given lecture number.

        """
        topic = next((t for t in course.outline.topics if t.number == lecture_number), None)
        if not topic:
            raise ValueError(f"No topic found for lecture number {lecture_number}")

        lecture_prompt = Template(course.settings.prompts.lecture).substitute(
            lecture_title=topic.title,
            course_title=course.title,
            course_outline=str(course.outline),
        )

        messages = [
            {"role": "system", "content": course.settings.prompts.system},
            {"role": "user", "content": lecture_prompt},
        ]

        self.log.info(
            f"Requesting lecture text for topic {topic.number}/{len(course.outline.topics)}: {topic.title}..."
        )

        response = await _retry_with_exponential_backoff(
            self.client.chat.completions.create,
            model=course.settings.text_model_lecture,
            messages=messages,
            max_completion_tokens=90000,
            logger=self.log,
        )

        if response.usage:
            course.generation_info.lecture_input_token_count += response.usage.prompt_tokens
            course.generation_info.lecture_output_token_count += response.usage.completion_tokens

        lecture_text = swap_words(response.choices[0].message.content.strip(), LLM_SMELLS)

        self.log.info(
            f"Got lecture text for topic {topic.number}/{len(course.outline.topics)} "
            f"@ {len(lecture_text)} chars: {topic.title}."
        )
        return CourseLecture(**topic.model_dump(), text=lecture_text)

    async def generate_lectures(self, course: Course) -> Course:
        """Generates the text for the lectures in the course outline.

        To generate an audio file for the Course generated by this method, call `generate_audio`.

        Returns:
            The `Course` with its `course.lectures` attribute set.
        """
        course.settings.output_directory = course.settings.output_directory.expanduser().resolve()
        lecture_tasks: list[asyncio.Task[CourseLecture]] = []

        with time_tracker(course.generation_info, "lecture_gen_elapsed_seconds"):
            async with asyncio.TaskGroup() as task_group:
                for topic in course.outline.topics:
                    task = task_group.create_task(
                        self._generate_lecture(course, topic.number),
                        name=f"generate_lecture_{topic.number}",
                    )
                    lecture_tasks.append(task)

        course.lectures = [t.result() for t in lecture_tasks]
        return course

    async def generate_image(self, course: Course) -> Course:
        """Generates cover art for the course with the given outline.

        The image is appropriate for use as cover art for the course text or audio.

        Returns:
            The `Course` with the `image_bytes` attribute set if successful.

        Raises:
            OpenAIError: If an error occurs during image generation.
        """
        course.settings.output_directory = course.settings.output_directory.expanduser().resolve()

        try:
            with time_tracker(course.generation_info, "image_gen_elapsed_seconds"):
                image_response = await _retry_with_exponential_backoff(
                    self.client.images.generate,
                    model=course.settings.image_model,
                    prompt=Template(course.settings.prompts.image).substitute(course_title=course.title),
                    n=1,
                    size="1024x1024",
                    response_format="b64_json",
                    quality="standard",
                    style="vivid",
                    logger=self.log,
                )

            if not image_response.data:
                self.log.warning(f"No image data returned for course '{course.title}'")
                return course

            course.generation_info.num_images_generated += 1
            image = image_response.data[0]
            image_bytes = base64.b64decode(image.b64_json)

            course.generation_info.image_file_path = course.settings.output_directory / Path(
                sanitize_filename(course.title)
            ).with_suffix(".png")
            course.generation_info.image_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.log.info(f"Saving image to {course.generation_info.image_file_path}")
            course.generation_info.image_file_path.write_bytes(image_bytes)

            # Save the course JSON now that we have the image path
            course.generation_info.image_file_path.with_suffix(".json").write_text(course.model_dump_json(indent=2))

            return course

        except OpenAIError as e:
            self.log.error("Encountered error generating image with OpenAI:")
            if isinstance(e, APIError):
                self.log.error(f"  Message: {e.message}")
                if e.request:
                    self.log.error(f"      URL: {e.request.url}")  # e.request is an httpx.Request
                if isinstance(e, APIStatusError) and e.response is not None:
                    self.log.error(f"   Status: {e.response.status_code} - {e.response.reason_phrase}")
            raise e

    async def _generate_speech_for_text_chunk(
        self,
        course: Course,
        text_chunk: str,
        chunk_num: int = 1,
    ) -> tuple[int, io.BytesIO]:
        """Generates an MP3 audio segment for a chunk of text using text-to-speech (TTS).

        Get text chunks to pass to this function from `utils.split_text_into_chunks`.

        Args:
            course: The course to generate TTS audio for.
            text_chunk: The text chunk to convert to speech.
            chunk_num: The chunk number (1-based).

        Returns:
            A tuple containing the chunk number and an in-memory bytes buffer of the generated audio.
        """
        self.log.info(f"Requesting TTS audio in voice '{course.settings.tts_voice}' for text chunk {chunk_num}...")

        while True:
            try:
                async with self.client.audio.speech.with_streaming_response.create(
                    model=course.settings.tts_model,
                    voice=course.settings.tts_voice,
                    input=text_chunk,
                ) as response:
                    audio_bytes = io.BytesIO()
                    async for data in response.iter_bytes():
                        audio_bytes.write(data)
                    audio_bytes.seek(0)
                    course.generation_info.tts_character_count += len(text_chunk)

                self.log.info(f"Got TTS audio for text chunk {chunk_num} in voice '{course.settings.tts_voice}'.")
                return chunk_num, audio_bytes

            except RateLimitError as exc:
                self.log.warning(f"RateLimitError while generating TTS for chunk {chunk_num}: {exc}")
                # Leverage the manual approach or the same exponential function for concurrency
                recommended_wait = _parse_openai_rate_limit_wait_time(str(exc))
                self.log.warning(f"Retrying TTS chunk {chunk_num} in {recommended_wait} seconds...")
                await asyncio.sleep(recommended_wait)

    async def generate_audio(self, course: Course) -> Course:
        """Generates an audio file from the combined text of the lectures in the given course using a TTS AI model.

        Returns:
            The `Course` with its `audio_file_path` attribute set, pointing to the TTS-generated file.
        """
        course.settings.output_directory = course.settings.output_directory.expanduser().resolve()
        if not tokenizer_available():
            download_tokenizer()

        # Combine all lecture texts, preceded by an AI disclosure
        course_text = (
            AI_DISCLOSURE
            + "\n\n"
            + course.title
            + "\n\n".join(f"Lecture {lecture.number}:\n\n{lecture.text}" for lecture in course.lectures)
        )
        course_chunks = split_text_into_chunks(course_text)
        speech_tasks: list[asyncio.Task[tuple[int, io.BytesIO]]] = []

        with time_tracker(course.generation_info, "audio_gen_elapsed_seconds"):
            async with asyncio.TaskGroup() as task_group:
                for chunk_num, chunk in enumerate(course_chunks, start=1):
                    task = task_group.create_task(
                        self._generate_speech_for_text_chunk(course, chunk, chunk_num),
                        name=f"generate_speech_chunk_{chunk_num}",
                    )
                    speech_tasks.append(task)

            audio_chunks = [task.result()[1] for task in sorted(speech_tasks, key=lambda t: t.result()[0])]

            # If the user generated an image for the course, embed it
            if course.generation_info.image_file_path and course.generation_info.image_file_path.exists():
                composer_tag = (
                    f"{course.settings.text_model_lecture} & "
                    f"{course.settings.tts_model} & "
                    f"{course.settings.image_model}"
                )
                cover_tag = io.BytesIO(course.generation_info.image_file_path.read_bytes())
            else:
                composer_tag = f"{course.settings.text_model_lecture} & {course.settings.tts_model}"
                cover_tag = None

            course.generation_info.audio_file_path = course.settings.output_directory / Path(
                sanitize_filename(course.title)
            ).with_suffix(".mp3")
            course.generation_info.audio_file_path.parent.mkdir(parents=True, exist_ok=True)

            version_string = get_top_level_version("okcourse")
            tags: dict[str, str] = {
                "title": course.title,
                "artist": f"{course.settings.tts_voice.capitalize()} & {course.settings.text_model_lecture} @ OpenAI",
                "composer": composer_tag,
                "album": "OK Courses",
                "genre": "Books & Spoken",
                "date": str(time.gmtime().tm_year),
                "author": f"Generated by AI with okcourse v{version_string}",
                "website": "https://github.com/mmacy/okcourse",
            }

            combined_mp3 = combine_mp3_buffers(
                audio_chunks,
                tags=tags,
                album_art=cover_tag,
                album_art_mime="image/png",
            )

            self.log.info(f"Saving audio to {course.generation_info.audio_file_path}")
            course.generation_info.audio_file_path.write_bytes(combined_mp3.getvalue())

        # Save the course JSON now that we have the audio path
        course.generation_info.audio_file_path.with_suffix(".json").write_text(course.model_dump_json(indent=2))

        return course

    async def generate_course(self, course: Course) -> Course:
        """Generates a complete course, including its outline, lectures, a cover image, and audio.

        Args:
            course: The course to generate.

        Returns:
            The `Course` with attributes populated by the generation process.
        """
        course = await self.generate_outline(course)
        course = await self.generate_lectures(course)
        course = await self.generate_image(course)
        course = await self.generate_audio(course)
        return course
