import io
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from pathlib import Path

import nltk
from openai import OpenAI
from pydub import AudioSegment

from .models import Lecture, LectureSeries, LectureSeriesOutline

NUM_LECTURES = 20
TEXT_MODEL = "gpt-4o"
SPEECH_MODEL = "tts-1"
SPEECH_VOICE = "nova"

DISCLAIMER = (
    "This is an AI-generated voice, not a human, presenting AI-generated content that might be biased or inaccurate."
)
SYSTEM_PROMPT = (
    "You are an esteemed college professor and expert in your field who regularly lectures graduate "
    "students. You have been asked by a major audiobook publisher to record an audiobook version of a lecture series. "
    "Your lecture style is professional, direct, and highly technical."
)

WORD_SWAPS = {
    "delve": "dig",
    "crucial": "important",
    "utilize": "use",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger()

llm_client = OpenAI()


def sanitize_filename(name: str) -> str:
    """Returns a filesystem-safe version of the given name.

    Strips leading/trailing whitespace, replaces spaces with underscores, and
    removes non-alphanumeric characters except for underscores and hyphens.

    Args:
        name: The string to sanitize.

    Returns:
        A sanitized string suitable for filenames.
    """
    name = name.strip().replace(" ", "_").lower()
    name = re.sub(r"[^\w\-]", "", name)
    return name


def format_time(seconds: float) -> str:
    """Formats a given number of seconds into H:MM:SS or M:SS format.

    Args:
        seconds: The number of seconds.

    Returns:
        A string formatted as H:MM:SS if hours > 0, otherwise M:SS.
    """
    td = timedelta(seconds=seconds)
    h, m, s = td.seconds // 3600, (td.seconds // 60) % 60, td.seconds % 60
    if h > 0:
        return f"{h}:{m:02}:{s:02}"
    return f"{m}:{s:02}"


def swap_words(text: str, swaps: dict[str, str]) -> str:
    """Swaps words in the given text.

    Args:
        text: The text to process.
        swaps: A dictionary of words to replace (keys) and their replacements (values).

    Returns:
        The text with swaps applied.
    """
    # Matches all keys as whole words
    pattern = r'\b(' + '|'.join(re.escape(word) for word in swaps.keys()) + r')\b'

    # Replace each match with its corresponding value from the swaps dictionary
    return re.sub(pattern, lambda match: swaps[match.group(0)], text)


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

    log.info("Requesting lecture series outline from LLM...")
    series_completion = llm_client.beta.chat.completions.parse(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": outline_prompt},
        ],
        response_format=LectureSeriesOutline,
    )
    series_outline = series_completion.choices[0].message.parsed

    # Reset the topic to exactly what was passed in since the LLM tends to add its own subtitle.
    log.info(f"Resetting lecture series topic to '{topic}' from LLM-provided '{series_outline.title}'")
    series_outline.title = topic

    return series_outline


def get_lecture_titles_from_outline(outline: str) -> list[str]:
    """Parses the given lecture outline and extracts a list of lecture titles.

    Args:
        outline: The text of the complete outline.

    Returns:
        list: List of lecture titles in the outline.
    """
    lecture_titles = []
    for line in outline.splitlines():
        match = re.match(r"^\s*\d+\.?\s*(.+)", line)
        if match:
            lecture_titles.append(match.group(1).strip().replace("*", ""))

    log.info(f"Got {len(lecture_titles)} lecture titles from outline.")
    return lecture_titles


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
        f"Generate the text for a lengthy lecture titled '{topic.title}' in a lecture series on "
        "'{series_outline.title}'. The lecture should be written in the style of a Great Courses audiobook by the "
        "Learning Company and should cover the topic in great detail. "
        "Omit Markdown from the lecture text as well as any tags, formatting markers, or headings that might interfere "
        "with text-to-speech processing. "
        "Ensure the content is original and does not duplicate content from the other lectures in the series.\n"
        f"Lecture Series Outline:\n{series_outline}"
    )

    log.info(
        f"Requesting lecture text from LLM for topic {topic.number}/{len(series_outline.topics)}: {topic.title}..."
    )
    response = llm_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    lecture_text = response.choices[0].message.content.strip()
    lecture_text = swap_words(lecture_text, WORD_SWAPS)

    log.info(f"Got lexture text from LLM for '{topic.title}'...")
    return Lecture(**topic.model_dump(), text=lecture_text)


def get_lectures(series_outline: LectureSeriesOutline) -> LectureSeries:
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


def _download_punkt() -> bool:
    """Downloads the NLTK 'punkt' tokenizer if not already downloaded.

    Returns:
        True if the tokenizer is available after the function call.
    """
    try:
        log.info("Checking for NLTK 'punkt' tokenizer...")
        nltk.data.find("tokenizers/punkt")
        log.info("Found NLTK 'punkt' tokenizer.")
        return True
    except LookupError:
        log.info("Downloading NLTK 'punkt' tokenizer...")
        nltk.download("punkt")
        log.info("Downloaded NLTK 'punkt' tokenizer.")
        return True


def _split_text_into_chunks(text: str, max_chunk_size: int = 4096) -> list[str]:
    """Splits text into chunks of approximately `max_chunk_size` characters.

    Args:
        text: The text to split.
        max_chunk_size: The maximum number of characters in each chunk.

    Returns:
        A list of text chunks equal to or less than the `max_chunk_size`.

    Raises:
        ValueError: If `max_chunk_size` < 1.
    """
    if max_chunk_size < 1:
        raise ValueError("max_chunk_size must be greater than 0")

    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length + 1 <= max_chunk_size:
            current_chunk.append(sentence)
            current_length += sentence_length + 1
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    log.info(f"Split text into {len(chunks)} chunks of ~{max_chunk_size} characters from {len(sentences)} sentences.")
    return chunks


def _generate_audio_chunk(chunk: str, chunk_num: int) -> tuple[int, AudioSegment]:
    """Generates an MP3 audio segment for a chunk of text using text-to-speech (TTS).

    Args:
        chunk: The text chunk to convert to speech.
        chunk_num: The chunk number.
        total_chunks: The total number of chunks.

    Returns:
        A tuple of (chunk_num, AudioSegment) for the generated audio.
    """
    log.info(f"Requesting TTS-generated audio for text chunk {chunk_num}...")
    with llm_client.audio.speech.with_streaming_response.create(
        # TODO: Allow runtime specification of the model and voice (and later, the service).
        model=SPEECH_MODEL,
        voice=SPEECH_VOICE,
        input=chunk,
    ) as response:
        audio_bytes = io.BytesIO()
        for data in response.iter_bytes():
            audio_bytes.write(data)
        audio_bytes.seek(0)
        log.info(f"Got TTS-generated audio for text chunk {chunk_num}.")
        return chunk_num, AudioSegment.from_file(audio_bytes, format="mp3")


def generate_audio(lecture_series: LectureSeries, output_file_path: str) -> bool:
    """Generates an audio file from the combined text of the lectures in the given lecture series.

    Args:
        lecture_series: The lecture series containing the lectures for which to generate audio.
        output_file_path: The location to write the audio file.

    Returns:
        Whether the audio file generation was successful.
    """
    if not _download_punkt():
        # If we don't have NLTK's 'punkt', we can't chunk the text to feed to the LLM for TTS.
        return False

    # Combine all lecture texts, including titles, preceded by the disclosure that it's all AI-generated
    lecture_series_text = (
        DISCLAIMER
        + "\n\n"
        + "\n\n".join(
            f"Lecture {lecture.number}, '{lecture.title}'.\n\n{lecture.text}" for lecture in lecture_series.lectures
        )
    )
    lecture_series_chunks = _split_text_into_chunks(lecture_series_text)

    # Process chunks in parallel to generate audio
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(_generate_audio_chunk, chunk, chunk_num): chunk_num
            for chunk_num, chunk in enumerate(lecture_series_chunks, start=1)
        }

        # Collect results as they complete
        audio_chunks = sorted(
            (future.result() for future in as_completed(futures)),
            key=lambda x: x[0],  # Sort by chunk number
        )

    # Combine all audio chunks into one audio segment
    log.info(f"Joining {len(audio_chunks)} audio chunks into one file...")
    lecture_series_audio = sum(
        (audio_chunk for _, audio_chunk in audio_chunks),
        AudioSegment.silent(duration=0),  # Start with silence
    )
    lecture_series_audio.export(output_file_path, format="mp3")

    return True


def run_generation(topic: str, num_lectures: int, generate_audio_file: bool = False) -> dict:
    """Generates a lecture series outline, text for each lecture in the series, and optionally audio of the series.

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
    lecture_series = get_lectures(series_outline)
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
        generate_audio(lecture_series, str(mp3_path))
        audio_gen_end = time.perf_counter()
        audio_gen_elapsed = audio_gen_end - audio_gen_start

    total_elapsed = outline_elapsed + series_generation_elapsed + audio_gen_elapsed

    return {
        "series_text_path": series_text_path,
        "audio_path": mp3_path if generate_audio_file else None,
        "total_time": total_elapsed,
    }
