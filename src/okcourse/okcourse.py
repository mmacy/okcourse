import asyncio
import base64
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
)
from .models import Lecture, Course, CourseOutline
from .utils import LLM_CLIENT, LOG, download_punkt, sanitize_filename, split_text_into_chunks, swap_words

__version__ = version("okcourse")


async def generate_course_outline(topic: str, num_lectures: int) -> CourseOutline:
    """Given the topic for a series of lectures in a course, generates a course outline using OpenAI.

    Args:
        topic: The course topic.
        num_lectures: The number of lectures that should be in the course.

    Returns:
        A detailed course outline in a Pydantic model instance.
    """
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

    # Reset the topic to exactly what was passed if the LLM modified the original (it sometimes adds its own subtitle)
    if course_outline.title != topic:
        LOG.info(f"Resetting course topic to '{topic}' from LLM-provided '{course_outline.title}'")
        course_outline.title = topic

    return course_outline


async def generate_lecture(course_outline: CourseOutline, lecture_number: int) -> Lecture:
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
        f"Got lexture text for topic {topic.number}/{len(course_outline.topics)} "
        f"@ {len(lecture_text)} chars: {topic.title}."
    )
    return Lecture(**topic.model_dump(), text=lecture_text)


async def generate_course_lectures(course_outline: CourseOutline) -> Course:
    """Generates the text for the lectures in the given course outline.

    To generate an audio file for the Course returned by this function, call `generate_course_audio()`.

    Args:
        course_outline: The outline of the course for which to generate lectures.

    Returns:
        The complete course containing all the lectures.
    """

    async def generate_course_lectures(course_outline: CourseOutline) -> Course:
        tasks = [generate_lecture(course_outline, topic.number) for topic in course_outline.topics]
        lectures = await asyncio.gather(*tasks)
        lectures.sort(key=lambda lecture: lecture.number)

        return Course(outline=course_outline, lectures=lectures)


def write_course_to_file(course: Course, output_dir: Path) -> Path:
    """Writes the full course, including its outline, to a JSON file.

    Args:
        course: The complete course, including the outline and all lectures in the series.
        output_dir: The directory where the files will be written.

    Returns:
        The path to the course JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    course_filename = f"{sanitize_filename(course.outline.title)}.json"
    course_text_path = output_dir / course_filename
    course_text_path.write_text(course.model_dump_json(), encoding="utf-8")

    return course_text_path


async def generate_speech_for_text_chunk(
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


async def generate_course_image(course_outline: CourseOutline, image_file_path: Path) -> Path | None:
    """Generates cover art for the course with the given outline.

    The image is appropriate for use as cover art for the course text or audio.

    Arguments:
        course_outline: The course outline to pass to the AI model to help guide its image generation.
        image_file_path: Where to save the generated cover image.

    Returns:
        Path to the generated cover image, or None if no cover image was generated.
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
        LOG.error("Failed to get image from the OpenAI API.")
        LOG.error(e.http_status)
        LOG.error(e.error)
        return None

    if image_response.data:
        output_dir = image_file_path.parent
        if not output_dir.exists():
            LOG.info(f"Creating directory for cover image: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)

        image = image_response.data[0]
        image_bytes = base64.b64decode(image.b64_json)
        image_file_path.write_bytes(image_bytes)
        return image_file_path
    else:
        # Got response, but no response data (somehow)
        return None


async def generate_course_audio(
    course: Course, output_file_path: str, voice: str = "nova", do_generate_cover_image: bool = False
) -> Path:
    """Generates an audio file from the combined text of the lectures in the given course using a TTS AI model.

    Args:
        course: The course containing the lectures for which to generate audio.
        output_file_path: The location to write the audio file.
        voice: The name of the voice to be used the course lecturer. Check `consants.VOICES` list for available names.
        do_generate_cover_image: Whether to request an AI-generated cover image for the audio file.

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

    # Process chunks in parallel to generate audio
    tasks = [
        generate_speech_for_text_chunk(chunk, voice, chunk_num)
        for chunk_num, chunk in enumerate(course_chunks, start=1)
    ]
    audio_chunks = await asyncio.gather(*tasks)
    audio_chunks.sort(key=lambda x: x[0])

    # Combine all audio chunks into one audio segment
    LOG.info(f"Joining {len(audio_chunks)} audio chunks into one file...")
    course_audio = sum(
        (audio_chunk for _, audio_chunk in audio_chunks),
        AudioSegment.silent(duration=0),  # Start with silence
    )

    # Get the cover image if specified
    if do_generate_cover_image:
        LOG.info("Getting cover image for the audio file...")
        cover_image_file = generate_course_image(
            course_outline=course.outline,
            image_file_path=Path(output_file_path).expanduser().resolve().with_suffix(".png"),
        )
    composer_tag = (
        f"{TEXT_MODEL} & {SPEECH_MODEL} & {IMAGE_MODEL}" if cover_image_file else f"{TEXT_MODEL} & {SPEECH_MODEL}"
    )
    cover_tag = str(cover_image_file) if cover_image_file else None

    # Tag the MP3 and save it to a file
    output_dir = Path(output_file_path).parent
    if not output_dir.exists():
        LOG.info(f"Creating directory {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    LOG.info("Exporting audio file...")
    course_audio.export(
        output_file_path,
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

    return Path(output_file_path).expanduser()


async def generate_course(
    topic: str, num_lectures: int, do_generate_audio_file: bool = False, do_generate_cover_art: bool = False
) -> dict:
    """Generates a complete course including its outline, text for its lectures, and optionally lecture audio.

    Args:
        topic: The topic of the course.
        num_lectures: Number of lectures within the series to generate.
        do_generate_audio_file: Whether to generate an audio file for the series.
        do_generate_cover_art: Wheter to generate a cover art image for the course and MP3, if generated.

    Returns:
        A dictionary containing:
          "course_text_path": Path to the course text file.
          "course_audio_path": Path to the audio file or `None`.
          "course_cover_path": Path to the cover art image or `None`.
          "total_seconds_elapsed": The total elapsed generation time in seconds.
    """

    outline_start_time = time.perf_counter()
    couse_outline = generate_course_outline(topic, num_lectures)
    outline_end_time = time.perf_counter()
    outline_elapsed = outline_end_time - outline_start_time

    course_generation_start_time = time.perf_counter()
    course = generate_course_lectures(couse_outline)
    course_generation_end_time = time.perf_counter()
    course_generation_elapsed = course_generation_end_time - course_generation_start_time

    output_dir = Path.cwd() / "lectures"
    course_text_path = write_course_to_file(course, output_dir)

    audio_gen_elapsed = 0.0
    mp3_path = output_dir / f"{sanitize_filename(course.outline.title)}.mp3"
    if do_generate_audio_file:
        if mp3_path.exists():
            mp3_path.unlink()
        audio_gen_start = time.perf_counter()
        mp3_path = generate_course_audio(course, str(mp3_path), do_generate_cover_art)
        audio_gen_end = time.perf_counter()
        audio_gen_elapsed = audio_gen_end - audio_gen_start

    total_elapsed = outline_elapsed + course_generation_elapsed + audio_gen_elapsed

    return {
        # TODO: Make this a Pydantic model (CourseMetadata) attribute on Course and return the Course
        "course_text_path": course_text_path,
        "course_audio_path": mp3_path if do_generate_audio_file else None,
        "course_cover_path": str(mp3_path.with_suffix(".png"))
        if do_generate_audio_file and do_generate_cover_art
        else None,
        "total_seconds_elapsed": total_elapsed,
    }
