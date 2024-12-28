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
from openai.types.image_model import ImageModel
from pydub import AudioSegment

from ..constants import (
    AI_DISCLAIMER,
    MAX_LECTURES,
)
from ..models import Course, CourseGenerationResult, CourseOutline, Lecture
from ..utils import (
    LLM_SMELLS,
    download_tokenizer,
    extract_literal_values_from_member,
    extract_literal_values_from_type,
    sanitize_filename,
    split_text_into_chunks,
    swap_words,
    tokenizer_available,
)
from .base import CourseGenerator

# from ..__init__ import __version__ as okcourse_version
_okcourse_version = "0.1.7"  # HACK: Avoid circular import


class AsyncOpenAICourseGenerator(CourseGenerator):
    """Uses the OpenAI API asynchronously to generate course content."""

    def __init__(self, *args, **kwargs):
        """Initializes the asynchronous OpenAI course generator.

        Args:
            *args: Additional positional arguments for the generator.
            **kwargs: Additional keyword arguments for the generator.
        """
        super().__init__(*args, **kwargs)
        self.client = AsyncOpenAI()
        self.image_models: list[str] = extract_literal_values_from_type(ImageModel)
        self.text_models: list[str] = extract_literal_values_from_type(ChatModel)
        self.speech_models: list[str] = extract_literal_values_from_type(SpeechModel)
        self.tts_voices: list[str] = extract_literal_values_from_member(SpeechCreateParams, "voice")

    async def generate_outline(self) -> CourseGenerationResult:
        """Generates a course outline for the course topic and the number of lectures specified in the settings.

        Set the course title in the generator's `settings` attribute before calling this method.

        Args:
            topic: The course topic.

        Returns:
            CourseGenerationResult: The result of the generation process with its `course.outline` attribute set.
        """
        if not self.settings.course_title or self.settings.course_title.strip() == "":
            msg = (
                "No course title in generator settings. Set the course title in the generator's settings before "
                "calling this method."
            )
            self.log.error(msg)
            raise ValueError(msg)
        if self.settings.num_lectures > MAX_LECTURES:
            msg = f"Number of lectures exceeds the maximum allowed ({MAX_LECTURES})."
            self.log.error(msg)
            raise ValueError(msg)

        outline_prompt_template = Template(self.settings.text_model_outline_prompt)
        outline_prompt = outline_prompt_template.substitute(
            num_lectures=self.settings.num_lectures, course_title=self.settings.course_title
        )

        self.log.info(f"Requesting outline for course '{self.settings.course_title}'...")
        course_completion = await self.client.beta.chat.completions.parse(
            model=self.settings.text_model,
            messages=[
                {"role": "system", "content": self.settings.text_model_system_prompt},
                {"role": "user", "content": outline_prompt},
            ],
            response_format=CourseOutline,
        )
        course_outline = course_completion.choices[0].message.parsed

        # Reset the topic to what was passed in if the LLM modified the original (it sometimes adds its own subtitle)
        if course_outline.title.lower() != self.settings.course_title.lower():
            self.log.info(
                f"Resetting course topic to '{self.settings.course_title}' (LLM returned '{course_outline.title}'"
            )
            course_outline.title = self.settings.course_title

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

        lecture_prompt_template = Template(self.settings.text_model_lecture_prompt)
        lecture_prompt = lecture_prompt_template.substitute(
            lecture_title=topic.title,
            course_title=course_outline.title,
            course_outline=str(course_outline),
        )

        self.log.info(
            f"Requesting lecture text for topic {topic.number}/{len(course_outline.topics)}: {topic.title}..."
        )
        response = await self.client.chat.completions.create(
            model=self.settings.text_model,
            messages=[
                {"role": "system", "content": self.settings.text_model_system_prompt},
                {"role": "user", "content": lecture_prompt},
            ],
            max_completion_tokens=15000,
        )
        lecture_text = response.choices[0].message.content.strip()
        lecture_text = swap_words(lecture_text, LLM_SMELLS)

        self.log.info(
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
                    name=f"generate_lecture_{topic.number}",)
                lecture_tasks.append(task)

        lectures = [lecture_task.result() for lecture_task in lecture_tasks]

        self.result.course.lectures = lectures

        # Lecture generation complete, so we can write out the course JSON file
        self.result.course_file_path = self.settings.output_directory / Path(
            sanitize_filename(course_outline.title)
        ).with_suffix(".json")
        self.result.course_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.result.course_file_path.write_text(self.result.model_dump_json(indent=2))

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
        self.log.info(f"Requesting TTS audio in voice '{voice}' for text chunk {chunk_num}...")
        async with self.client.audio.speech.with_streaming_response.create(
            model=self.settings.tts_model,
            voice=voice,
            input=text_chunk,
        ) as response:
            audio_bytes = io.BytesIO()
            async for data in response.iter_bytes():
                audio_bytes.write(data)
            audio_bytes.seek(0)
            self.log.info(f"Got TTS audio for text chunk {chunk_num} in voice '{voice}'.")

            return chunk_num, AudioSegment.from_file(audio_bytes, format="mp3")

    async def generate_image(self) -> CourseGenerationResult:
        """Generates cover art for the course with the given outline.

        The image is appropriate for use as cover art for the course text or audio.

        Returns:
            The results of the generation process with the `image_bytes` attribute set.
        """
        course_outline = self.result.course.outline
        image_prompt_template = Template(self.settings.image_model_prompt)
        image_prompt = image_prompt_template.substitute(course_title=course_outline.title)
        try:
            image_response = await self.client.images.generate(
                model=self.settings.image_model,
                prompt=image_prompt,
                n=1,
                size="1024x1024",
                response_format="b64_json",
                quality="standard",
                style="vivid",
            )
            if not image_response.data:
                self.log.warning(f"No image data returned for course '{course_outline.title}'")
                return None

            image = image_response.data[0]
            image_bytes = base64.b64decode(image.b64_json)

            self.result.image_file_path = self.settings.output_directory / Path(
                sanitize_filename(course_outline.title)
            ).with_suffix(".png")
            self.result.image_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.log.info(f"Saving image to {self.result.image_file_path}")
            self.result.image_file_path.write_bytes(image_bytes)

            return self.result

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

        self.log.info(f"Joining {len(audio_chunks)} audio chunks into one file...")
        course_audio = sum(
            (audio_chunk for _, audio_chunk in audio_chunks),
            AudioSegment.silent(duration=0),  # Start with silence
        )

        if self.settings.generate_image and self.result.image_file_path and self.result.image_file_path.exists():
            composer_tag = f"{self.settings.text_model} & {self.settings.tts_model} & {self.settings.image_model}"
            cover_tag = str(self.result.image_file_path)
        else:
            composer_tag = f"{self.settings.text_model} & {self.settings.tts_model}"

        self.log.info("Exporting audio file...")

        self.result.audio_file_path = self.settings.output_directory / Path(
            sanitize_filename(self.result.course.title)
        ).with_suffix(".mp3")
        self.result.audio_file_path.parent.mkdir(parents=True, exist_ok=True)

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
                "comment": f"Generated by AI with okcourse v{_okcourse_version} - https://github.com/mmacy/okcourse",
            },
        )

        return self.result
