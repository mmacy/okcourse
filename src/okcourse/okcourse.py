# lecture_generator.py
import io
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


@dataclass
class Lecture:
    number: int
    title: str
    text: str


def get_openai_client() -> OpenAI:
    return OpenAI()


def sanitize_filename(name: str) -> str:
    name = name.strip().replace(" ", "_").lower()
    name = re.sub(r"[^\w\-]", "", name)
    return name


def format_time(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    h, m, s = td.seconds // 3600, (td.seconds // 60) % 60, td.seconds % 60
    return f"{h}:{m:02}:{s:02}" if h > 0 else f"{m}:{s:02}"


def generate_lecture_series_outline(client: OpenAI, topic: str, num_lectures: int) -> tuple[list[str], str]:
    prompt = (
        f"Provide a detailed outline for a {num_lectures}-part lecture series for a graduate-level course on "
        f"'{topic}'. List each lecture title numbered. Each lecture should have four subtopics listed after the "
        "lecture title. Respond only with the outline, omitting any other commentary."
    )
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {"role": "user", "content": prompt},
        ],
    )

    outline_text = response.choices[0].message.content
    lecture_titles = []
    for line in outline_text.splitlines():
        match = re.match(r"^\s*\d+\.?\s*(.+)", line)
        if match:
            lecture_titles.append(match.group(1).strip().replace("*", ""))
        if len(lecture_titles) >= num_lectures:
            break
    return lecture_titles, outline_text


def get_lecture(client: OpenAI, topic: str, lecture_title: str, outline: str, idx: int) -> Lecture:
    prompt = (
        f"Generate the text for a lengthy lecture titled '{lecture_title}' in a lecture series on '{topic}'. "
        "The lecture should be written in the style of a Great Courses audiobook by the Learning Company and should "
        "cover the topic in great detail. "
        "Omit Markdown from the lecture text as well as any tags, formatting markers, or headings that might interfere "
        "with text-to-speech processing. Omit temporal references to the lecture (e.g. 'today'), as well as references "
        "to yourself or the audience. "
        "Ensure the content is original and does not duplicate content from the other lectures in the series.\n"
        f"Lecture Series Outline:\n{outline}"
    )

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {"role": "user", "content": prompt},
        ],
    )

    lecture_text = response.choices[0].message.content.strip()
    return Lecture(idx, lecture_title, lecture_text)


def get_lectures(client: OpenAI, lecture_titles: list[str], topic: str, outline_text: str) -> list[Lecture]:
    lectures: list[Lecture] = []
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(get_lecture, client, topic, title, outline_text, idx): idx
            for idx, title in enumerate(lecture_titles, start=1)
        }

        for future in as_completed(futures):
            lecture = future.result()
            lectures.append(lecture)

    lectures.sort(key=lambda lecture: lecture.number)
    return lectures


def write_aggregate_file(
    lecture_series_title: str, lectures: list[Lecture], lecture_outline: str, output_dir: Path
) -> tuple[Path, Path]:
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


def download_punkt():
    try:
        nltk.data.find("tokenizers/punkt")
        return True
    except LookupError:
        nltk.download("punkt")
        return True


def split_text_into_chunks(text: str, max_chunk_size: int = 4096) -> list[str]:
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

    return chunks


def generate_audio_chunk(client: OpenAI, chunk: str, chunk_num: int, total_chunks: int):
    with client.audio.speech.with_streaming_response.create(
        model=SPEECH_MODEL,
        voice=SPEECH_VOICE,
        input=chunk,
    ) as response:
        audio_bytes = io.BytesIO()
        for data in response.iter_bytes():
            audio_bytes.write(data)
        audio_bytes.seek(0)
        return chunk_num, AudioSegment.from_file(audio_bytes, format="mp3")


def generate_audio(client: OpenAI, lectures: list[Lecture], output_file_path: str):
    if download_punkt():
        lecture_series_text = DISCLAIMER + "\n\n"
        lecture_series_text += "\n\n".join(lecture.text for lecture in lectures)
        lecture_series_chunks = split_text_into_chunks(lecture_series_text)

        total_chunks = len(lecture_series_chunks)
        results = []
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(generate_audio_chunk, client, chunk, chunk_num, total_chunks): chunk_num
                for chunk_num, chunk in enumerate(lecture_series_chunks, start=1)
            }

            for future in as_completed(futures):
                chunk_num, lecture_audio_chunk = future.result()
                results.append((chunk_num, lecture_audio_chunk))

        results.sort(key=lambda x: x[0])
        lecture_series_audio = AudioSegment.silent(duration=0)
        for _, lecture_audio_chunk in results:
            lecture_series_audio += lecture_audio_chunk

        lecture_series_audio.export(output_file_path, format="mp3")


def run_generation(topic: str, num_lectures: int, generate_audio_file: bool):
    client = get_openai_client()

    outline_start_time = time.perf_counter()
    lecture_titles, outline_text = generate_lecture_series_outline(client, topic, num_lectures)
    outline_end_time = time.perf_counter()
    outline_elapsed = outline_end_time - outline_start_time

    series_generation_start_time = time.perf_counter()
    lectures = get_lectures(client, lecture_titles, topic, outline_text)
    series_generation_end_time = time.perf_counter()
    series_generation_elapsed = series_generation_end_time - series_generation_start_time

    output_dir = Path.cwd() / "lectures"
    aggregate_path, outline_path = write_aggregate_file(topic, lectures, outline_text, output_dir)

    audio_gen_elapsed = 0.0
    mp3_path = output_dir / f"{sanitize_filename(topic)}.mp3"
    if generate_audio_file:
        if mp3_path.exists():
            mp3_path.unlink()
        audio_gen_start = time.perf_counter()
        generate_audio(client, lectures, str(mp3_path))
        audio_gen_end = time.perf_counter()
        audio_gen_elapsed = audio_gen_end - audio_gen_start

    total_elapsed = outline_elapsed + series_generation_elapsed + audio_gen_elapsed

    return {
        "outline_path": outline_path,
        "aggregate_path": aggregate_path,
        "audio_path": mp3_path if generate_audio_file else None,
        "total_time": total_elapsed,
    }
