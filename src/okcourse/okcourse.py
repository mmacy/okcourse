import asyncio
import base64
import io
import time
from importlib.metadata import version
from pathlib import Path

from openai import OpenAIError
from pydub import AudioSegment

from .constants import (
    AI_DISCLAIMER,
    IMAGE_MODEL,
    IMAGE_PROMPT,
    LLM_SMELLS,
    SPEECH_MODEL,
    SYSTEM_PROMPT,
    TEXT_MODEL,
    MAX_LECTURES,
)
from .models import Course, CourseOutline, Lecture
from .utils import LLM_CLIENT, LOG, download_punkt, split_text_into_chunks, swap_words

__version__ = version("okcourse")

#############
# ASYNC
#############


async def generate_course_outline_async(topic: str, num_lectures: int) -> CourseOutline:
    """Given the topic for a series of lectures in a course, generates a course outline using OpenAI.

    Args:
        topic: The course topic.
        num_lectures: The number of lectures that should be in the course.

    Returns:
        A detailed course outline in a Pydantic model instance.
    """
    if num_lectures > MAX_LECTURES:
        raise ValueError(f"Number of lectures exceeds the maximum allowed ({MAX_LECTURES}).")

    outline_prompt = (
        f"Provide a detailed outline for {num_lectures} lectures in a graduate-level course on '{topic}'. "
        f"List each lecture title numbered. Each lecture should have four subtopics listed after the "
        "lecture title. Respond only with the outline, omitting any other commentary."
    )

    LOG.info("Requesting course outline from LLM...")
    course_completion = await LLM_CLIENT.beta.chat.completions.parse(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": outline_prompt},
        ],
        response_format=CourseOutline,
    )
    course_outline = course_completion.choices[0].message.parsed

    # Reset the topic to what was passed in if the LLM modified the original (it sometimes adds its own subtitle)
    if course_outline.title.lower() != topic.lower():
        LOG.info(f"Resetting course topic to '{topic}' (LLM returned '{course_outline.title}'")
        course_outline.title = topic

    return course_outline


async def generate_lecture_async(course_outline: CourseOutline, lecture_number: int) -> Lecture:
    """Generates a lecture for the topic with the specified number in the given outline.

    Args:
        outline: The outline of the course containing lecture topics and their subtopics.
        number: The position number of the lecture to generate.

    Returns:
        A Lecture object representing the lecture for the given number.
    """
    topic = next((t for t in course_outline.topics if t.number == lecture_number), None)
    if not topic:
        raise ValueError(f"No topic found for lecture number {lecture_number}")
    prompt = (
        f"Generate the complete unabridged text for a lecture titled '{topic.title}' in a graduate-level course named "
        f"'{course_outline.title}'. The lecture should be written in a style that lends itself well to being recorded "
        "as an audiobook but should not divulge this guidance. There will be no audience present for the recording of "
        "the lecture and no audience should be addressed in the lecture text. Cover the lecture topic in great detail "
        "while keeping in mind the advanced education level of the listeners of the lecture. "
        "Omit Markdown from the lecture text as well as any tags, formatting markers, or headings that might interfere "
        "with text-to-speech processing. Ensure the content is original and does not duplicate content from the other "
        f"lectures in the series:\n{str(course_outline)}"
    )

    LOG.info(f"Requesting lecture text for topic {topic.number}/{len(course_outline.topics)}: {topic.title}...")
    response = await LLM_CLIENT.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=15000,
    )
    lecture_text = response.choices[0].message.content.strip()
    lecture_text = swap_words(lecture_text, LLM_SMELLS)

    LOG.info(
        f"Got lecture text for topic {topic.number}/{len(course_outline.topics)} "
        f"@ {len(lecture_text)} chars: {topic.title}."
    )
    return Lecture(**topic.model_dump(), text=lecture_text)


async def generate_course_lectures_async(course_outline: CourseOutline) -> Course:
    """Generates the text for the lectures in the given course outline.

    To generate an audio file for the Course returned by this function, call `generate_course_audio()`.

    Args:
        course_outline: The outline of the course for which to generate lectures.

    Returns:
        The complete course containing all the lectures.
    """
    tasks = [generate_lecture_async(course_outline, topic.number) for topic in course_outline.topics]
    lectures = await asyncio.gather(*tasks)
    lectures.sort(key=lambda lecture: lecture.number)

    return Course(outline=course_outline, lectures=lectures)


async def generate_speech_for_text_chunk_async(
    text_chunk: str, voice: str = "nova", chunk_num: int = 1
) -> tuple[int, AudioSegment]:
    """Generates an MP3 audio segment for a chunk of text using text-to-speech (TTS).

    Get text chunks to pass to this function from ``utils.split_text_into_chunks``.

    Args:
        chunk: The text chunk to convert to speech.
        chunk_num: (Optional) The chunk number.

    Returns:
        A tuple of (chunk_num, AudioSegment) for the generated audio.
    """
    LOG.info(f"Requesting TTS audio in voice '{voice}' for text chunk {chunk_num}...")
    async with LLM_CLIENT.audio.speech.with_streaming_response.create(
        # TODO: Allow runtime specification of the model (and later, the service).
        model=SPEECH_MODEL,
        voice=voice,
        input=text_chunk,
    ) as response:
        audio_bytes = io.BytesIO()
        async for data in response.iter_bytes():
            audio_bytes.write(data)
        audio_bytes.seek(0)
        LOG.info(f"Got TTS audio for text chunk {chunk_num} in voice '{voice}'.")
        return chunk_num, AudioSegment.from_file(audio_bytes, format="mp3")


async def generate_course_image_async(course_outline: CourseOutline, image_file_path: Path = None) -> bytes:
    """Generates cover art for the course with the given outline.

    The image is appropriate for use as cover art for the course text or audio.

    Arguments:
        course_outline: The course outline to pass to the AI model to help guide its image generation.
        image_file_path: Where to save the image that's generated by the AI model.

    Returns:
        The PNG image in bytes if successful, otherwise None.
    """
    try:
        image_response = await LLM_CLIENT.images.generate(
            model=IMAGE_MODEL,
            prompt=IMAGE_PROMPT + course_outline.title,
            n=1,
            size="1024x1024",
            response_format="b64_json",
            quality="standard",
            style="vivid",
        )
    except OpenAIError as e:
        LOG.error(f"Failed to get image from the OpenAI API:\n{e}")
        return None

    if image_response.data:
        image = image_response.data[0]
        image_bytes = base64.b64decode(image.b64_json)

        if image_file_path:
            output_dir = image_file_path.parent
            if not output_dir.exists():
                LOG.info(f"Creating directory for cover image: {output_dir}")
                output_dir.mkdir(parents=True, exist_ok=True)
            LOG.info(f"Writing image bytes to: {str(image_file_path)}")
            image_file_path.write_bytes(image_bytes)

        return image_bytes
    else:
        # Got response, but no response data (somehow)
        return None


async def generate_course_audio_async(
    course: Course, output_file_path: Path, voice: str = "nova", cover_image_path: Path = None
) -> Path:
    """Generates an audio file from the combined text of the lectures in the given course using a TTS AI model.

    Args:
        course: The course containing the lectures for which to generate audio.
        output_file_path: The location to write the audio file.
        voice: The name of the voice to be used the course lecturer. Check `consants.VOICES` list for available names.
        cover_image_path: Path to the PNG file to use as the cover image for the MP3.

    Returns:
        The path to the TTS-generated audio file.
    """
    if not download_punkt():
        # If we don't have NLTK's 'punkt', we can't chunk the text to feed to the LLM for TTS.
        return False

    # Combine all lecture texts, including titles, preceded by the disclosure that it's all AI-generated
    course_text = (
        AI_DISCLAIMER
        + "\n\n"
        + "\n\n".join(f"Lecture {lecture.number}:\n\n{lecture.text}" for lecture in course.lectures)
    )
    course_chunks = split_text_into_chunks(course_text)

    # Process chunks asynchronously to generate audio
    tasks = [
        generate_speech_for_text_chunk_async(chunk, voice, chunk_num)
        for chunk_num, chunk in enumerate(course_chunks, start=1)
    ]
    audio_chunks = await asyncio.gather(*tasks)
    audio_chunks.sort(key=lambda x: x[0])  # Sort by chunk number

    # Combine all audio chunks into one audio segment
    LOG.info(f"Joining {len(audio_chunks)} audio chunks into one file...")
    course_audio = sum(
        (audio_chunk for _, audio_chunk in audio_chunks),
        AudioSegment.silent(duration=0),  # Start with silence
    )

    if cover_image_path:
        composer_tag = f"{TEXT_MODEL} & {SPEECH_MODEL} & {IMAGE_MODEL}"
        cover_tag = str(cover_image_path)
    else:
        composer_tag = f"{TEXT_MODEL} & {SPEECH_MODEL}"
    # Tag the MP3 and save it to a file
    output_dir = output_file_path.parent
    if not output_dir.exists():
        LOG.info(f"Creating directory {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    LOG.info("Exporting audio file...")
    course_audio.export(
        str(output_file_path),
        format="mp3",
        cover=cover_tag,
        tags={
            "title": course.outline.title,
            "artist": f"{voice.capitalize()} @ OpenAI",
            "composer": composer_tag,
            "album": "OK Courses",
            "genre": "Books & Spoken",
            "date": str(time.gmtime().tm_year),
            "comment": f"Generated by AI with okcourse v{__version__} - https://github.com/mmacy/okcourse",
        },
    )

    return output_file_path


#############
# SYNC
#############


def generate_course_outline(topic: str, num_lectures: int) -> CourseOutline:
    """Synchronous wrapper for generate_course_outline_async."""
    return asyncio.run(generate_course_outline_async(topic, num_lectures))


def generate_lecture(course_outline: CourseOutline, lecture_number: int) -> Lecture:
    """Synchronous wrapper for generate_lecture_async."""
    return asyncio.run(generate_lecture_async(course_outline, lecture_number))


def generate_course_lectures(course_outline: CourseOutline) -> Course:
    """Synchronous wrapper for generate_course_lectures_async."""
    return asyncio.run(generate_course_lectures_async(course_outline))


def generate_speech_for_text_chunk(
    text_chunk: str, voice: str = "nova", chunk_num: int = 1
) -> tuple[int, AudioSegment]:
    """Synchronous wrapper for generate_speech_for_text_chunk_async."""
    return asyncio.run(generate_speech_for_text_chunk_async(text_chunk, voice, chunk_num))


def generate_course_image(course_outline: CourseOutline, image_file_path: Path) -> Path | None:
    """Synchronous wrapper for generate_course_image_async."""
    return asyncio.run(generate_course_image_async(course_outline, image_file_path))


def generate_course_audio(
    course: Course, output_file_path: str, voice: str = "nova", do_generate_cover_image: bool = False
) -> Path:
    """Synchronous wrapper for generate_course_audio_async."""
    return asyncio.run(generate_course_audio_async(course, output_file_path, voice, do_generate_cover_image))
