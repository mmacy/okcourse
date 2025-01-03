"""The `async_openai` module contains the [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator] class."""

import asyncio
import base64
import io
import time
from pathlib import Path
from string import Template

from openai import APIError, APIStatusError, AsyncOpenAI, OpenAIError
from openai.types.audio.speech_create_params import SpeechCreateParams
from openai.types.audio.speech_model import SpeechModel
from openai.types.chat_model import ChatModel
from openai.types.completion_usage import (
    CompletionUsage,
    CompletionTokensDetails,
    PromptTokensDetails,
)
from openai.types.image_model import ImageModel
from pydub import AudioSegment

from ...constants import (
    AI_DISCLOSURE,
    MAX_LECTURES,
)
from ...models import Course, CourseOutline, Lecture
from ...utils import (
    LLM_SMELLS,
    download_tokenizer,
    extract_literal_values_from_member,
    extract_literal_values_from_type,
    get_logger,
    get_top_level_version,
    sanitize_filename,
    split_text_into_chunks,
    swap_words,
    tokenizer_available,
)
from ..base import CourseGenerator


class OpenAIAsyncGenerator(CourseGenerator):
    """Uses the OpenAI API to generate course content asynchronously.

    Use the `OpenAIAsyncGenerator` to generate a course outline, lectures, cover image, and audio file for a course.

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

        course.details.okcourse_version = get_top_level_version("okcourse")

        if course.settings.log_level:
            log_file = course.settings.output_directory / Path(__name__).with_suffix(".log")
            self.log = get_logger(
                source_name=__name__,
                level=course.settings.log_level,
                file_path=log_file if course.settings.log_to_file else None,
            )

            if course.settings.log_to_file:
                self.log.info(f"Logging to file: {log_file}")

        self.client = AsyncOpenAI()

        # Populate lists of available models and voices for possible use presenting options to the user
        self.image_models: list[str] = extract_literal_values_from_type(ImageModel)
        self.text_models: list[str] = extract_literal_values_from_type(ChatModel)
        self.speech_models: list[str] = extract_literal_values_from_type(SpeechModel)
        self.tts_voices: list[str] = extract_literal_values_from_member(SpeechCreateParams, "voice")

        # OpenAI pricing as of 2024-01-02
        # gpt-4o    | $0.00250 / 1K input tokens
        # gpt-4o    | $0.01000 / 1K output tokens
        # dall-e-3  | $0.040 / image Standard 1024×1024
        # tts-1     | $0.015 / 1K characters
        # {
        #     "okcourse_version": "0.1.8",
        #     "input_token_count": 2079,
        #     "output_token_count": 2710,
        #     "tts_character_count": 15896,
        #     "num_images_generated": 1,
        #     "audio_file_path": "/Users/mmacy/.okcourse_files/calculating_openai_api_usage_cost.mp3",
        #     "image_file_path": "/Users/mmacy/.okcourse_files/calculating_openai_api_usage_cost.png"
        # }

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

        outline_prompt_template = Template(course.settings.text_model_outline_prompt)
        outline_prompt = outline_prompt_template.substitute(
            num_lectures=course.settings.num_lectures, course_title=course.title
        )

        self.log.info(f"Requesting outline for course '{course.title}'...")
        outline_completion = await self.client.beta.chat.completions.parse(
            model=course.settings.text_model,
            messages=[
                {"role": "system", "content": course.settings.text_model_system_prompt},
                {"role": "user", "content": outline_prompt},
            ],
            response_format=CourseOutline,
        )
        if outline_completion.usage:
            course.details.input_token_count += outline_completion.usage.prompt_tokens
            course.details.output_token_count += outline_completion.usage.completion_tokens
        generated_outline = outline_completion.choices[0].message.parsed

        # Reset the topic to what was passed in if the LLM modified the original (it sometimes adds its own subtitle)
        if generated_outline.title.lower() != course.title.lower():
            self.log.info(f"Resetting course topic to '{course.title}' (LLM returned '{generated_outline.title}'")
            generated_outline.title = course.title

        course.outline = generated_outline
        return course

    async def _generate_lecture(self, course: Course, lecture_number: int) -> Lecture:
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

        lecture_prompt_template = Template(course.settings.text_model_lecture_prompt)
        lecture_prompt = lecture_prompt_template.substitute(
            lecture_title=topic.title,
            course_title=course.title,
            course_outline=str(course.outline),
        )

        self.log.info(
            f"Requesting lecture text for topic {topic.number}/{len(course.outline.topics)}: {topic.title}..."
        )
        response = await self.client.chat.completions.create(
            model=course.settings.text_model,
            messages=[
                {"role": "system", "content": course.settings.text_model_system_prompt},
                {"role": "user", "content": lecture_prompt},
            ],
            max_completion_tokens=15000,
        )
        if response.usage:
            course.details.input_token_count += response.usage.prompt_tokens
            course.details.output_token_count += response.usage.completion_tokens
        lecture_text = response.choices[0].message.content.strip()
        lecture_text = swap_words(lecture_text, LLM_SMELLS)

        self.log.info(
            f"Got lecture text for topic {topic.number}/{len(course.outline.topics)} "
            f"@ {len(lecture_text)} chars: {topic.title}."
        )
        return Lecture(**topic.model_dump(), text=lecture_text)

    async def generate_lectures(self, course: Course) -> Course:
        """Generates the text for the lectures in the course outline in the settings.

        To generate an audio file for the Course generated by this method, call `generate_audio`.

        Returns:
            The Course with its `course.lectures` attribute set.
        """
        lecture_tasks = []

        async with asyncio.TaskGroup() as task_group:
            for topic in course.outline.topics:
                task = task_group.create_task(
                    self._generate_lecture(course, topic.number),
                    name=f"generate_lecture_{topic.number}",
                )
                lecture_tasks.append(task)

        course.lectures = [lecture_task.result() for lecture_task in lecture_tasks]

        return course

    async def _generate_speech_for_text_chunk(
        self, course: Course, text_chunk: str, chunk_num: int = 1
    ) -> tuple[int, AudioSegment]:
        """Generates an MP3 audio segment for a chunk of text using text-to-speech (TTS).

        Get text chunks to pass to this function from ``utils.split_text_into_chunks``.

        Args:
            course: The course to generate TTS audio for.
            text_chunk: The text chunk to convert to speech.
            chunk_num: (Optional) The chunk number.

        Returns:
            A tuple of (chunk_num, AudioSegment) for the generated audio.
        """
        self.log.info(f"Requesting TTS audio in voice '{course.settings.tts_voice}' for text chunk {chunk_num}...")
        async with self.client.audio.speech.with_streaming_response.create(
            model=course.settings.tts_model,
            voice=course.settings.tts_voice,
            input=text_chunk,
        ) as response:
            audio_bytes = io.BytesIO()
            async for data in response.iter_bytes():
                audio_bytes.write(data)
            audio_bytes.seek(0)
            course.details.tts_character_count += len(text_chunk)
            self.log.info(f"Got TTS audio for text chunk {chunk_num} in voice '{course.settings.tts_voice}'.")

            return chunk_num, AudioSegment.from_file(audio_bytes, format="mp3")

    async def generate_image(self, course: Course) -> Course:
        """Generates cover art for the course with the given outline.

        The image is appropriate for use as cover art for the course text or audio.

        Returns:
            The results of the generation process with the `image_bytes` attribute set.

        Raises:
            OpenAIError: If an error occurs during image generation.
        """
        image_prompt_template = Template(course.settings.image_model_prompt)
        image_prompt = image_prompt_template.substitute(course_title=course.title)
        try:
            image_response = await self.client.images.generate(
                model=course.settings.image_model,
                prompt=image_prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json",
                quality="standard",
                style="vivid",
            )
            if not image_response.data:
                self.log.warning(f"No image data returned for course '{course.title}'")
                return None

            course.details.num_images_generated += 1
            image = image_response.data[0]
            image_bytes = base64.b64decode(image.b64_json)

            course.details.image_file_path = course.settings.output_directory / Path(
                sanitize_filename(course.title)
            ).with_suffix(".png")
            course.details.image_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.log.info(f"Saving image to {course.details.image_file_path}")
            course.details.image_file_path.write_bytes(image_bytes)

            # Save the course as JSON now that we have the image path
            course.details.image_file_path.with_suffix(".json").write_text(course.model_dump_json(indent=2))

            return course

        except OpenAIError as e:
            self.log.error("Encountered error generating image with OpenAI:")
            if e is APIError:
                self.log.error(f"  Message: {e.message}")
                self.log.error(f"      URL: {e.request.url}")  # e.request is an httpx.Request
                if e is APIStatusError:
                    self.log.error(
                        # Guaranteed to have a complete response as this is bubbled up from httpx
                        f"   Status: {e.response.status_code} - {e.response.reason_phrase}"
                    )
            raise e

    async def generate_audio(self, course: Course) -> Course:
        """Generates an audio file from the combined text of the lectures in the given course using a TTS AI model.

        Returns:
            The course with its `audio_file_path` attribute set which points to the TTS-generated file.
        """
        if not tokenizer_available():
            download_tokenizer()

        # Combine all lecture texts, including titles, preceded by the disclosure that it's all AI-generated
        course_text = (
            AI_DISCLOSURE
            + "\n\n"
            + course.title
            + "\n\n".join(f"Lecture {lecture.number}:\n\n{lecture.text}" for lecture in course.lectures)
        )
        course_chunks = split_text_into_chunks(course_text)

        speech_tasks = []
        async with asyncio.TaskGroup() as task_group:
            for chunk_num, chunk in enumerate(course_chunks, start=1):
                task = task_group.create_task(
                    self._generate_speech_for_text_chunk(
                        course=course,
                        text_chunk=chunk,
                        chunk_num=chunk_num,
                    ),
                )
                speech_tasks.append(task)

        audio_chunks = [speech_task.result() for speech_task in speech_tasks]

        self.log.info(f"Joining {len(audio_chunks)} audio chunks into one file...")
        course_audio = sum(
            (audio_chunk for _, audio_chunk in audio_chunks),
            AudioSegment.silent(duration=0),  # Start with silence
        )

        if course.details.image_file_path and course.details.image_file_path.exists():
            composer_tag = f"{course.settings.text_model} & {course.settings.tts_model} & {course.settings.image_model}"
            cover_tag = str(course.details.image_file_path)
        else:
            composer_tag = f"{course.settings.text_model} & {course.settings.tts_model}"
            cover_tag = None

        course.details.audio_file_path = course.settings.output_directory / Path(
            sanitize_filename(course.title)
        ).with_suffix(".mp3")
        course.details.audio_file_path.parent.mkdir(parents=True, exist_ok=True)

        version_string = get_top_level_version("okcourse")

        self.log.info(f"Saving audio to {course.details.audio_file_path}")
        course_audio.export(
            str(course.details.audio_file_path),
            format="mp3",
            cover=cover_tag,
            tags={
                "title": course.title,
                "artist": f"{course.settings.tts_voice.capitalize()} @ OpenAI",
                "composer": composer_tag,
                "album": "OK Courses",
                "genre": "Books & Spoken",
                "date": str(time.gmtime().tm_year),
                "comment": f"Generated by AI with okcourse v{version_string} - https://github.com/mmacy/okcourse",
            },
        )

        # Save the course as JSON now that we have the audio file path
        course.details.audio_file_path.with_suffix(".json").write_text(course.model_dump_json(indent=2))

        return course

    async def generate_course(self, course: Course) -> Course:
        """Generates a complete course, including its outline, lectures, a cover image, and audio.

        Args:
            course: The course to generate.

        Returns:
            Course: The course with all attributes populated by the generation process.
        """

        course = await self.generate_outline(course)
        course = await self.generate_lectures(course)
        course = await self.generate_image(course)
        course = await self.generate_audio(course)

        return course
