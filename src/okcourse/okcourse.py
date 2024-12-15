import base64
import io
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAIError
from pydub import AudioSegment

from .constants import (
    AI_DISCLAIMER,
    IMAGE_MODEL,
    IMAGE_PROMPT,
    LLM_SMELLS,
    SPEECH_MODEL,
    SPEECH_VOICE,
    SYSTEM_PROMPT,
    TEXT_MODEL,
)
from .models import Lecture, LectureSeries, LectureSeriesOutline
from .utils import LLM_CLIENT, LOG, download_punkt, sanitize_filename, split_text_into_chunks, swap_words


def generate_lecture_series_outline(topic: str, num_lectures: int) -> LectureSeriesOutline:
    """Given the topic for a series of lectures, generates a series outline using OpenAI.

    Args:
        topic: The lecture series topic.
        num_lectures: The number of lectures that should be in the series.

    Returns:
        A detailed lecture outline in a Pydantic model instance.
    """
    outline_prompt = (
        f"Provide a detailed outline for a {num_lectures}-part lecture series for a graduate-level course on "
        f"'{topic}'. List each lecture title numbered. Each lecture should have four subtopics listed after the "
        "lecture title. Respond only with the outline, omitting any other commentary."
    )

    LOG.info("Requesting lecture series outline from LLM...")
    series_completion = LLM_CLIENT.beta.chat.completions.parse(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": outline_prompt},
        ],
        response_format=LectureSeriesOutline,
    )
    series_outline = series_completion.choices[0].message.parsed

    # Reset the topic to exactly what was passed if the LLM modified the original (it sometimes adds its own subtitle)
    if series_outline.title != topic:
        LOG.info(f"Resetting lecture series topic to '{topic}' from LLM-provided '{series_outline.title}'")
        series_outline.title = topic

    return series_outline


def get_lecture(series_outline: LectureSeriesOutline, lecture_number: int) -> Lecture:
    """Generates a lecture for the topic with the specified number in the given outline.

    Args:
        outline: The outline of the lecture series containing lecture topics and their subtopics.
        number: The position number of the lecture to generate.

    Returns:
        A Lecture object representing the lecture for the given number.
    """
    topic = next((t for t in series_outline.topics if t.number == lecture_number), None)
    if not topic:
        raise ValueError(f"No topic found for lecture number {lecture_number}")
    prompt = (
        f"Generate the complete unabridged text for a college lecture titled '{topic.title}' in a lecture series on "
        "'{series_outline.title}'. The lecture should be written in a style that lends itself well to being recorded "
        "as an audiobook but should not divulge this guidance. Cover the lecture topic in great detail. "
        "Omit Markdown from the lecture text as well as any tags, formatting markers, or headings that might interfere "
        "with text-to-speech processing. "
        "Ensure the content is original and does not duplicate content from the other lectures in the series.\n"
        f"Lecture Series Outline:\n{series_outline}"
    )

    LOG.info(f"Requesting lecture text for topic {topic.number}/{len(series_outline.topics)}: {topic.title}...")
    response = LLM_CLIENT.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    lecture_text = response.choices[0].message.content.strip()
    lecture_text = swap_words(lecture_text, LLM_SMELLS)

    LOG.info(f"Got lexture text for topic {topic.number}/{len(series_outline.topics)}: {topic.title}.")
    return Lecture(**topic.model_dump(), text=lecture_text)


def generate_text_for_lectures_in_series(series_outline: LectureSeriesOutline) -> LectureSeries:
    """Generates the text for the lectures in the given lecture series outline.

    Args:
        series_outline: The outline of the lecture series for which to generate lectures.

    Returns:
        The complete lecture series containing all the lectures.
    """
    with ThreadPoolExecutor() as executor:
        lectures = list(
            executor.map(
                # Use a lambda here to provide both the outline and lecture number
                lambda topic: get_lecture(series_outline, topic.number),
                series_outline.topics,
            )
        )
    lectures.sort(key=lambda lecture: lecture.number)

    return LectureSeries(outline=series_outline, lectures=lectures)


def write_lecture_series_to_file(lecture_series: LectureSeries, output_dir: Path) -> Path:
    """Writes the full lecture series, including its outline, to disk.

    Args:
        lecture_series: The complete lecture series, including the outline and all lectures in the series.
        output_dir: The directory where the files will be written.

    Returns:
        The path to the lecture series text file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    lecture_series_filename = f"{sanitize_filename(lecture_series.outline.title)}.txt"
    lecture_series_text_path = output_dir / lecture_series_filename
    lecture_series_text_path.write_text(str(lecture_series), encoding="utf-8")

    return lecture_series_text_path


def _generate_tts_audio_for_text_chunk(text_chunk: str, chunk_num: int) -> tuple[int, AudioSegment]:
    """Generates an MP3 audio segment for a chunk of text using text-to-speech (TTS).

    Get text chunks to pass to this function from ``utils.split_text_into_chunks``.

    Args:
        chunk: The text chunk to convert to speech.
        chunk_num: The chunk number.

    Returns:
        A tuple of (chunk_num, AudioSegment) for the generated audio.
    """
    LOG.info(f"Requesting TTS-generated audio for text chunk {chunk_num}...")
    with LLM_CLIENT.audio.speech.with_streaming_response.create(
        # TODO: Allow runtime specification of the model and voice (and later, the service).
        model=SPEECH_MODEL,
        voice=SPEECH_VOICE,
        input=text_chunk,
    ) as response:
        audio_bytes = io.BytesIO()
        for data in response.iter_bytes():
            audio_bytes.write(data)
        audio_bytes.seek(0)
        LOG.info(f"Got TTS-generated audio for text chunk {chunk_num}.")
        return chunk_num, AudioSegment.from_file(audio_bytes, format="mp3")


def generate_cover_image(lecture_outline: LectureSeriesOutline, image_file_path: Path) -> Path | None:
    """Generates cover art for the lecture with the given outline.

    The image is appropriate for use as the cover or album art for the lecture series text or audio.

    Arguments:
        lecture_outline: The lecture series outline to pass to the AI model to help guide its image generation.
        image_file_path: Where to save the generated cover image.

    Returns:
        Path to the generated cover image, or None if no cover image was generated.
    """
    try:
        image_response = LLM_CLIENT.images.generate(
            model=IMAGE_MODEL,
            prompt=IMAGE_PROMPT + lecture_outline.title,
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
        image = image_response.data[0]
        LOG.info("Got cover image.")
        image_bytes = base64.b64decode(image.b64_json)
        image_file_path.write_bytes(image_bytes)
        return image_file_path
    else:
        # Got response, but no response data (somehow)
        return None


def generate_audio_for_lectures_in_series(lecture_series: LectureSeries, output_file_path: str) -> bool:
    """Generates an audio file from the combined text of the lectures in the given lecture series.

    Args:
        lecture_series: The lecture series containing the lectures for which to generate audio.
        output_file_path: The location to write the audio file.

    Returns:
        Whether the audio file generation was successful.
    """
    if not download_punkt():
        # If we don't have NLTK's 'punkt', we can't chunk the text to feed to the LLM for TTS.
        return False

    # Combine all lecture texts, including titles, preceded by the disclosure that it's all AI-generated
    lecture_series_text = (
        AI_DISCLAIMER
        + "\n\n"
        + "\n\n".join(f"Lecture {lecture.number}:\n\n{lecture.text}" for lecture in lecture_series.lectures)
    )
    lecture_series_chunks = split_text_into_chunks(lecture_series_text)

    # Process chunks in parallel to generate audio
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(_generate_tts_audio_for_text_chunk, chunk, chunk_num): chunk_num
            for chunk_num, chunk in enumerate(lecture_series_chunks, start=1)
        }

        # Collect results as they complete
        audio_chunks = sorted(
            (future.result() for future in as_completed(futures)),
            key=lambda x: x[0],  # Sort by chunk number
        )

    # Combine all audio chunks into one audio segment
    LOG.info(f"Joining {len(audio_chunks)} audio chunks into one file...")
    lecture_series_audio = sum(
        (audio_chunk for _, audio_chunk in audio_chunks),
        AudioSegment.silent(duration=0),  # Start with silence
    )
    LOG.info("Getting cover image for the audio file...")
    cover_image_file = generate_cover_image(
        lecture_outline=lecture_series.outline,
        image_file_path=Path(output_file_path).expanduser().resolve().with_suffix(".png"),
    )
    LOG.info("Exporting audio file...")
    lecture_series_audio.export(
        output_file_path,
        format="mp3",
        cover=str(cover_image_file) if cover_image_file else None,
        tags={
            "title": lecture_series.outline.title,
            "artist": f"AI: {TEXT_MODEL} & {SPEECH_MODEL}",
            "album": "OK Courses",
            "comment": "https://github.com/mmacy/okcourse",
        }
    )

    return True


def generate_complete_lecture_series(topic: str, num_lectures: int, generate_audio_file: bool = False) -> dict:
    """Generates a complete lecture series including its outline, text for its lectures, and optionally lecture audio.

    Args:
        topic: The topic of the lecture series.
        num_lectures: Number of lectures within the series to generate.
        generate_audio_file: Whether to generate an audio file for the series.

    Returns:
        A dictionary containing:
          "series_text_path": Path to the lecture series text file.
          "audio_path": Path to the audio file or `None`.
          "total_time": The total elapsed generation time in seconds.
    """

    outline_start_time = time.perf_counter()
    series_outline = generate_lecture_series_outline(topic, num_lectures)
    outline_end_time = time.perf_counter()
    outline_elapsed = outline_end_time - outline_start_time

    series_generation_start_time = time.perf_counter()
    lecture_series = generate_text_for_lectures_in_series(series_outline)
    series_generation_end_time = time.perf_counter()
    series_generation_elapsed = series_generation_end_time - series_generation_start_time

    output_dir = Path.cwd() / "lectures"
    series_text_path = write_lecture_series_to_file(lecture_series, output_dir)

    audio_gen_elapsed = 0.0
    mp3_path = output_dir / f"{sanitize_filename(lecture_series.outline.title)}.mp3"
    if generate_audio_file:
        if mp3_path.exists():
            mp3_path.unlink()
        audio_gen_start = time.perf_counter()
        generate_audio_for_lectures_in_series(lecture_series, str(mp3_path))
        audio_gen_end = time.perf_counter()
        audio_gen_elapsed = audio_gen_end - audio_gen_start

    total_elapsed = outline_elapsed + series_generation_elapsed + audio_gen_elapsed

    return {
        "series_text_path": series_text_path,
        "audio_path": mp3_path if generate_audio_file else None,
        "total_time": total_elapsed,
    }
