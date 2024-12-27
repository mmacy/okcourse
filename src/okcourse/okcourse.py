"""Main module for the okcourse package. Primary interface for generating course outlines, lectures, and audio files."""

import asyncio
import base64
import io
import logging
import time
from abc import ABC, abstractmethod
from importlib.metadata import version
from pathlib import Path
from string import Template

from openai import APIError, APIStatusError, AsyncOpenAI, OpenAIError
from pydub import AudioSegment

from .constants import (
    AI_DISCLAIMER,
    DEFAULT_IMAGE_PROMPT,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TEXT_MODEL,
    DEFAULT_TTS_MODEL,
    LLM_SMELLS,
    MAX_LECTURES,
    TTS_VOICES,
)
from .models import Course, CourseOutline, Lecture, CourseGenerationResult
from .settings import CourseGeneratorSettings
from .utils import download_tokenizer, split_text_into_chunks, swap_words, tokenizer_available

__version__ = version("okcourse")

log = logging.getLogger(__name__)

client = AsyncOpenAI()

default_generator_settings = CourseGeneratorSettings(
    course_title=None,
    num_lectures=2,
    output_directory=Path("~/.okcourse").expanduser(),
    generate_image=True,
    generate_audio=True,
    log_level=logging.INFO,
    text_model=DEFAULT_TEXT_MODEL,
    text_model_system_prompt=DEFAULT_SYSTEM_PROMPT,
    text_model_outline_prompt=None,  # Set during course generation
    text_model_lecture_prompt=None,  # Set during lecture generation
    image_model="dall-e-3",
    image_model_prompt=DEFAULT_IMAGE_PROMPT,
    tts_model=DEFAULT_TTS_MODEL,
    tts_voice=TTS_VOICES[0],
    max_concurrent_requests=32,
)


class CourseGenerator(ABC):
    """
    Abstract base class for generating a course outline, its lectures, a cover image, and audio for the course.

    Attributes:
        settings: The settings used for course generation.

    Subclasses must implement the abstract methods to generate the course outline, lectures, image, and audio.
    """

    def __init__(self, generation_settings: CourseGeneratorSettings = default_generator_settings):
        self.settings: CourseGeneratorSettings = generation_settings
        self.result: CourseGenerationResult = CourseGenerationResult(settings=self.settings)

    @abstractmethod
    def generate_outline(self, course_title: str | None = None) -> CourseGenerationResult:
        """Generates an outline for a course with the specified title.

        Args:
            course_title: The title of the course. If not provided, the title from the settings is used.

        Returns:
            CourseGenerationResult: The result of the generation process with its `course.outline` attribute set.
        """
        pass

    @abstractmethod
    def generate_lectures(self) -> CourseGenerationResult:
        """Generates lectures for the course and saves the course and its outline to the path specified in the settings.

        Returns:
            CourseGenerationResult: The result of the generation process with its `course.lectures` and `course_file`
            attributes set.
        """
        pass

    @abstractmethod
    def generate_image(self) -> CourseGenerationResult:
        """Generates a cover image for the course and saves it to the path specified in the settings.

        Returns:
            CourseGenerationResult: The result of the generation process with its `image_file` attribute set.
        """
        pass

    @abstractmethod
    def generate_audio(self) -> CourseGenerationResult:
        """Generates audio for the course and saves it to the path specified in the settings.

        Args:
            output_path: The path where the audio file will be saved.
        """
        pass


class AsyncOpenAICourseGenerator(CourseGenerator):
    """Uses the OpenAI API asynchronously to generate course content."""

    async def generate_outline(self) -> CourseGenerationResult:
        """Generates a course outline for the course topic and the number of lectures specified in the settings.

        Set the course title in the generator's `settings` attribute before calling this method.

        Args:
            topic: The course topic.

        Returns:
            CourseGenerationResult: The result of the generation process with its `course.outline` attribute set.
        """
        if not self.settings.course_title or self.settings.course_title.strip() == "":
            raise ValueError(
                "No course title in generator settings. Set the course title in the generator's settings before "
                "calling this method."
            )
        if self.settings.num_lectures > MAX_LECTURES:
            raise ValueError(f"Number of lectures exceeds the maximum allowed ({MAX_LECTURES}).")

        outline_prompt_template = Template(
            "Provide a detailed outline for ${num_lectures} lectures in a graduate-level course on '${topic}'. "
            "List each lecture title numbered. Each lecture should have four subtopics listed after the "
            "lecture title. Respond only with the outline, omitting any other commentary."
        )
        self.settings.text_model_outline_prompt = outline_prompt_template.substitute(
            num_lectures=self.settings.num_lectures, topic=self.settings.course_title
        )

        log.info("Requesting course outline from LLM...")
        course_completion = await client.beta.chat.completions.parse(
            model=self.settings.text_model,
            messages=[
                {"role": "system", "content": self.settings.text_model_system_prompt},
                {"role": "user", "content": self.settings.text_model_outline_prompt},
            ],
            response_format=CourseOutline,
        )
        course_outline = course_completion.choices[0].message.parsed

        # Reset the topic to what was passed in if the LLM modified the original (it sometimes adds its own subtitle)
        if course_outline.title.lower() != topic.lower():
            log.info(f"Resetting course topic to '{topic}' (LLM returned '{course_outline.title}'")
            course_outline.title = topic

        self.result.course = Course(outline=course_outline)
        return self.result

    async def _generate_lecture(self, course_outline: CourseOutline, lecture_number: int) -> Lecture:
        """Generates a lecture for the topic with the specified number in the given outline.

        Args:
            course_outline: The outline of the course containing lecture topics and their subtopics.
            lecture_number: The position number of the lecture to generate.

        Returns:
            A Lecture object representing the lecture for the given number.
        """
        topic = next((t for t in course_outline.topics if t.number == lecture_number), None)
        if not topic:
            raise ValueError(f"No topic found for lecture number {lecture_number}")
        lecture_prompt = (
            "Generate the complete unabridged text for a lecture titled '${lecture_title}' in a graduate-level course named "  # noqa: E501
            "'${course_title}'. The lecture should be written in a style that lends itself well to being recorded "  # noqa: E501
            "as an audiobook but should not divulge this guidance. There will be no audience present for the recording of "  # noqa: E501
            "the lecture and no audience should be addressed in the lecture text. Cover the lecture topic in great detail "  # noqa: E501
            "while keeping in mind the advanced education level of the listeners of the lecture. "
            "Omit Markdown from the lecture text as well as any tags, formatting markers, or headings that might interfere "  # noqa: E501
            "with text-to-speech processing. Ensure the content is original and does not duplicate content from the other "  # noqa: E501
            "lectures in the series:\n${course_outline}"
        )
        self.settings.text_model_lecture_prompt = lecture_prompt

        log.info(f"Requesting lecture text for topic {topic.number}/{len(course_outline.topics)}: {topic.title}...")
        response = await client.chat.completions.create(
            model=self.settings.text_model,
            messages=[
                {"role": "system", "content": self.settings.text_model_system_prompt},
                {"role": "user", "content": self.settings.text_model_lecture_prompt},
            ],
            max_completion_tokens=15000,
        )
        lecture_text = response.choices[0].message.content.strip()
        lecture_text = swap_words(lecture_text, LLM_SMELLS)

        log.info(
            f"Got lecture text for topic {topic.number}/{len(course_outline.topics)} "
            f"@ {len(lecture_text)} chars: {topic.title}."
        )
        return Lecture(**topic.model_dump(), text=lecture_text)

    async def generate_lectures(self) -> CourseGenerationResult:
        """Generates the text for the lectures in the course outline in the settings.

        To generate an audio file for the Course generated by this method, call `generate_course_audio`.

        Returns:
            The results of the generation process with the `course.lectures` attribute set.
        """
        course_outline = self.result.course.outline
        lecture_tasks = []

        async with asyncio.TaskGroup() as task_group:
            for topic in course_outline.topics:
                task = task_group.create_task(
                    self._generate_lecture(course_outline, topic.number),
                )
                lecture_tasks.append(task)

        lectures = [lecture_task.result() for lecture_task in lecture_tasks]

        self.result.course.lectures = lectures
        return self.result

    async def _generate_speech_for_text_chunk(
        self, text_chunk: str, voice: str = "nova", chunk_num: int = 1
    ) -> tuple[int, AudioSegment]:
        """Generates an MP3 audio segment for a chunk of text using text-to-speech (TTS).

        Get text chunks to pass to this function from ``utils.split_text_into_chunks``.

        Args:
            text_chunk: The text chunk to convert to speech.
            voice: (Optional) The name of the voice to use for the TTS.
            chunk_num: (Optional) The chunk number.

        Returns:
            A tuple of (chunk_num, AudioSegment) for the generated audio.
        """
        log.info(f"Requesting TTS audio in voice '{voice}' for text chunk {chunk_num}...")
        async with client.audio.speech.with_streaming_response.create(
            model=self.settings.tts_model,
            voice=voice,
            input=text_chunk,
        ) as response:
            audio_bytes = io.BytesIO()
            async for data in response.iter_bytes():
                audio_bytes.write(data)
            audio_bytes.seek(0)
            log.info(f"Got TTS audio for text chunk {chunk_num} in voice '{voice}'.")

            return chunk_num, AudioSegment.from_file(audio_bytes, format="mp3")

    async def generate_image(self) -> CourseGenerationResult:
        """Generates cover art for the course with the given outline.

        The image is appropriate for use as cover art for the course text or audio.

        Returns:
            The results of the generation process with the `image_bytes` attribute set.
        """
        course_outline = self.result.course.outline
        try:
            image_response = await client.images.generate(
                model=self.settings.image_model,
                prompt=DEFAULT_IMAGE_PROMPT + course_outline.title,
                n=1,
                size="1024x1024",
                response_format="b64_json",
                quality="standard",
                style="vivid",
            )
            if not image_response.data:
                log.warning(f"No image data returned for course '{course_outline.title}'")
                return None, None

            image = image_response.data[0]
            image_bytes = base64.b64decode(image.b64_json)

            image_file_path = self.result.image_file_path
            image_file_path.parent.mkdir(parents=True, exist_ok=True)
            log.info(f"Saving image to {image_file_path}")
            image_file_path.write_bytes(image_bytes)

            self.result.image_bytes = image_bytes
            return self.result

        except OpenAIError as e:
            log.error("Encountered error generating image with OpenAI:")
            if e is APIError:
                log.error(f"  Message: {e.message}")
                log.error(f"      URL: {e.request.url}")  # e.request is an httpx.Request
                if e is APIStatusError:
                    log.error(
                        # Guaranteed to have a complete response as this is bubbled up from httpx
                        f"   Status: {e.response.status_code} - {e.response.reason_phrase}"
                    )
            raise e

    async def generate_audio(self) -> CourseGenerationResult:
        """Generates an audio file from the combined text of the lectures in the given course using a TTS AI model.

        Returns:
            THe results of the generation process.
        """
        if not tokenizer_available():
            download_tokenizer()

        # Combine all lecture texts, including titles, preceded by the disclosure that it's all AI-generated
        course_text = (
            AI_DISCLAIMER
            + "\n\n"
            + self.result.course.title
            + "\n\n".join(f"Lecture {lecture.number}:\n\n{lecture.text}" for lecture in self.result.course.lectures)
        )
        course_chunks = split_text_into_chunks(course_text)

        speech_tasks = []
        async with asyncio.TaskGroup() as task_group:
            for chunk_num, chunk in enumerate(course_chunks, start=1):
                task = task_group.create_task(
                    self._generate_speech_for_text_chunk(chunk, self.settings.tts_voice, chunk_num),
                )
                speech_tasks.append(task)

        audio_chunks = [speech_task.result() for speech_task in speech_tasks]

        log.info(f"Joining {len(audio_chunks)} audio chunks into one file...")
        course_audio = sum(
            (audio_chunk for _, audio_chunk in audio_chunks),
            AudioSegment.silent(duration=0),  # Start with silence
        )

        if self.settings.generate_image:
            composer_tag = f"{self.settings.text_model} & {self.settings.tts_model} & {self.settings.image_model}"
            cover_tag = str(self.result.image_file_path)
        else:
            composer_tag = f"{self.settings.text_model} & {self.settings.tts_model}"

        if not self.settings.output_directory.exists():
            log.info(f"Creating directory {self.settings.output_directory}")
            self.settings.output_directory.mkdir(parents=True, exist_ok=True)

        log.info("Exporting audio file...")
        course_audio.export(
            str(self.result.audio_file_path),
            format="mp3",
            cover=cover_tag if self.settings.generate_image else None,
            tags={
                "title": self.result.course.title,
                "artist": f"{self.settings.tts_voice.capitalize()} @ OpenAI",
                "composer": composer_tag,
                "album": "OK Courses",
                "genre": "Books & Spoken",
                "date": str(time.gmtime().tm_year),
                "comment": f"Generated by AI with okcourse v{__version__} - https://github.com/mmacy/okcourse",
            },
        )

        return self.result


# def generate_course_outline(topic: str, num_lectures: int) -> CourseOutline:
#     """Synchronous wrapper for generate_course_outline_async."""
#     return asyncio.run(generate_course_outline_async(topic, num_lectures))


# def generate_lecture(course_outline: CourseOutline, lecture_number: int) -> Lecture:
#     """Synchronous wrapper for generate_lecture_async."""
#     return asyncio.run(generate_lecture_async(course_outline, lecture_number))


# def generate_course_lectures(course_outline: CourseOutline) -> Course:
#     """Synchronous wrapper for generate_course_lectures_async."""
#     return asyncio.run(generate_course_lectures_async(course_outline))


# def generate_speech_for_text_chunk(
#     text_chunk: str, voice: str = "nova", chunk_num: int = 1
# ) -> tuple[int, AudioSegment]:
#     """Synchronous wrapper for generate_speech_for_text_chunk_async."""
#     return asyncio.run(generate_speech_for_text_chunk_async(text_chunk, voice, chunk_num))


# def generate_course_image(
#     course_outline: CourseOutline, image_file_path: Path = None
# ) -> tuple[bytes | None, Path | None]:
#     """Synchronous wrapper for generate_course_image_async."""
#     return asyncio.run(generate_course_image_async(course_outline, image_file_path))


# def generate_course_audio(
#     course: Course, output_file_path: Path, voice: str = "nova", cover_image_path: Path = None
# ) -> Path:
#     """Synchronous wrapper for generate_course_audio_async."""
#     return asyncio.run(generate_course_audio_async(course, output_file_path, voice, cover_image_path))
