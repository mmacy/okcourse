import io
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import nltk
from openai import OpenAI
from pydub import AudioSegment

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger()

llm_client = OpenAI()


@dataclass
class Lecture:
    """Represents a lecture in the series.

    Attributes:
        number: The lecture number in the series.
        title: The lecture title.
        text: The full lecture text content.
    """

    number: int
    title: str
    text: str


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


def generate_lecture_series_outline(topic: str, num_lectures: int) -> str:
    """Given the topic for a series of lectures, generates a series outline using OpenAI.

    Args:
        topic: The lecture series topic.
        num_lectures: The number of lectures that should be in the series.

    Returns:
        A detailed lecture outline.
    """
    prompt = (
        f"Provide a detailed outline for a {num_lectures}-part lecture series for a graduate-level course on "
        f"'{topic}'. List each lecture title numbered. Each lecture should have four subtopics listed after the "
        "lecture title. Respond only with the outline, omitting any other commentary."
    )

    log.info("Requesting lecture outline from LLM...")
    response = llm_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    lecture_outline = response.choices[0].message.content

    return lecture_outline


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


def get_lecture(topic: str, lecture_title: str, outline: str, idx: int) -> Lecture:
    """Generates the text content for a single lecture.

    Args:
        topic: The topic of the lecture series.
        lecture_title: The title of this specific lecture.
        outline: The full lecture series outline.
        idx: The lecture number.

    Returns:
        A Lecture instance containing the generated lecture content.
    """
    prompt = (
        f"Generate the text for a lengthy lecture titled '{lecture_title}' in a lecture series on '{topic}'. "
        "The lecture should be written in the style of a Great Courses audiobook by the Learning Company and should "
        "cover the topic in great detail. "
        "Omit Markdown from the lecture text as well as any tags, formatting markers, or headings that might interfere "
        "with text-to-speech processing. Omit temporal references to the lecture, as well as references "
        "to yourself or the audience. "
        "Ensure the content is original and does not duplicate content from the other lectures in the series.\n"
        f"Lecture Series Outline:\n{outline}"
    )

    log.info(f"Requesting lexture text from LLM for '{lecture_title}'...")
    response = llm_client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    lecture_text = response.choices[0].message.content.strip()

    log.info(f"Got lexture text from LLM for '{lecture_title}'...")
    return Lecture(idx, lecture_title, lecture_text)


def get_lectures(lecture_titles: list[str], topic: str, outline_text: str) -> list[Lecture]:
    """Generates the text of the lectures in the given lecture series outline.

    Args:
        lecture_titles: A list of lecture titles.
        topic: The topic of the lecture series.
        outline_text: The full outline text of the lecture series.

    Returns:
        A list of Lecture instances.
    """
    lectures = []
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_lecture, topic, title, outline_text, idx): idx
            for idx, title in enumerate(lecture_titles, start=1)
        }
        for future in as_completed(futures):
            lecture = future.result()
            lectures.append(lecture)
    lectures.sort(key=lambda lec: lec.number)
    return lectures


def write_lecture_series_to_file(
    lecture_series_title: str,
    lectures: list[Lecture],
    lecture_outline: str,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Writes aggregate lecture text and outline files to disk.

    Args:
        lecture_series_title: The main title of the lecture series.
        lectures: A list of Lecture objects.
        lecture_outline: The full outline text.
        output_dir: The directory where the files will be written.

    Returns:
        A tuple containing:
          - The path to the aggregate text file.
          - The path to the outline text file.
    """
    sanitized_title = sanitize_filename(lecture_series_title)
    aggregate_filename = f"{sanitized_title}.txt"
    outline_filename = f"{sanitized_title}_outline.txt"
    output_dir.mkdir(parents=True, exist_ok=True)

    aggregate_content = DISCLAIMER + "\n\n"
    aggregate_content += "\n\n".join(
        f"Lecture {lecture.number}: {lecture.title}\n\n{lecture.text}" for lecture in lectures
    )

    aggregate_path = output_dir / aggregate_filename
    aggregate_path.write_text(aggregate_content, encoding="utf-8")

    outline_path = output_dir / outline_filename
    outline_path.write_text(lecture_outline, encoding="utf-8")

    return aggregate_path, outline_path


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

    log.info(f"Split text into {len(chunks)} chunks of ~{max_chunk_size} characters from {len(sentences)}.")
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


def generate_audio(lectures: list[Lecture], output_file_path: str) -> None:
    """Generates an audio file from the combined text of the given list of `Lecture` objects.

    Use ``split_text_into_chunks`` to get a list of `Lecture` objects to pass to this function.

    Args:
        client: An initialized OpenAI client.
        lectures: A list of `Lecture` instances.
        output_file_path: The location to write the audio file.
    """
    if _download_punkt():
        lecture_series_text = DISCLAIMER + "\n\n"
        lecture_series_text += "\n\n".join(lec.text for lec in lectures)
        lecture_series_chunks = _split_text_into_chunks(lecture_series_text)

        audio_chunks = []
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(_generate_audio_chunk, chunk, chunk_num): chunk_num
                for chunk_num, chunk in enumerate(lecture_series_chunks, start=1)
            }

            for future in as_completed(futures):
                chunk_num, lecture_audio_chunk = future.result()
                audio_chunks.append((chunk_num, lecture_audio_chunk))

        audio_chunks.sort(key=lambda x: x[0])
        lecture_series_audio = AudioSegment.silent(duration=0)
        for _, lecture_audio_chunk in audio_chunks:
            lecture_series_audio += lecture_audio_chunk

        # TODO: Support other audio formats.
        log.info(f"Joining {len(audio_chunks)} audio chunks into one file...")
        lecture_series_audio.export(output_file_path, format="mp3")


def run_generation(topic: str, num_lectures: int, generate_audio_file: bool = False) -> dict:
    """Generates a lecture series outline, text for each lecture in the series, and optionally audio of the series.

    Args:
        topic: The topic of the lecture series.
        num_lectures: Number of lectures within the series to generate.
        generate_audio_file: Whether to generate an audio file for the series.

    Returns:
        A dictionary containing:
          "outline_path": Path to the outline text file.
          "aggregate_path": Path to the aggregate lecture text file.
          "audio_path": Path to the audio file or `None`.
          "total_time": The total elapsed generation time in seconds.
    """

    outline_start_time = time.perf_counter()
    outline_text = generate_lecture_series_outline(topic, num_lectures)
    lecture_titles = get_lecture_titles_from_outline(outline_text)
    outline_end_time = time.perf_counter()
    outline_elapsed = outline_end_time - outline_start_time

    series_generation_start_time = time.perf_counter()
    lectures = get_lectures(lecture_titles, topic, outline_text)
    series_generation_end_time = time.perf_counter()
    series_generation_elapsed = series_generation_end_time - series_generation_start_time

    output_dir = Path.cwd() / "lectures"
    aggregate_path, outline_path = write_lecture_series_to_file(topic, lectures, outline_text, output_dir)

    audio_gen_elapsed = 0.0
    mp3_path = output_dir / f"{sanitize_filename(topic)}.mp3"
    if generate_audio_file:
        if mp3_path.exists():
            mp3_path.unlink()
        audio_gen_start = time.perf_counter()
        generate_audio(lectures, str(mp3_path))
        audio_gen_end = time.perf_counter()
        audio_gen_elapsed = audio_gen_end - audio_gen_start

    total_elapsed = outline_elapsed + series_generation_elapsed + audio_gen_elapsed

    return {
        "outline_path": outline_path,
        "aggregate_path": aggregate_path,
        "audio_path": mp3_path if generate_audio_file else None,
        "total_time": total_elapsed,
    }
