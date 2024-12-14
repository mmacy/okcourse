import logging
from datetime import timedelta

import nltk
import re
from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger()


LLM_CLIENT = OpenAI()


def download_punkt() -> bool:
    """Downloads the NLTK 'punkt' tokenizer if not already downloaded.

    Returns:
        True if the tokenizer is available after the function call.
    """
    try:
        LOG.info("Checking for NLTK 'punkt' tokenizer...")
        nltk.data.find("tokenizers/punkt")
        LOG.info("Found NLTK 'punkt' tokenizer.")
        return True
    except LookupError:
        LOG.info("Downloading NLTK 'punkt' tokenizer...")
        nltk.download("punkt")
        LOG.info("Downloaded NLTK 'punkt' tokenizer.")
        return True


def split_text_into_chunks(text: str, max_chunk_size: int = 4096) -> list[str]:
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

    LOG.info(f"Split text into {len(chunks)} chunks of ~{max_chunk_size} characters from {len(sentences)} sentences.")
    return chunks


def sanitize_filename(name: str) -> str:
    """Returns a filesystem-safe version of the given string.

    - Strips leading and trailing whitespace
    - Replaces spaces with underscores
    - Removes non-alphanumeric characters except for underscores and hyphens
    - Tranforms to lowercase

    Args:
        name: The string to sanitize.

    Returns:
        A sanitized string suitable for filenames.
    """
    name = name.strip().replace(" ", "_").lower()
    name = re.sub(r"[^\w\-]", "", name)
    return name


def get_duration_string_from_seconds(seconds: float) -> str:
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


def swap_words(text: str, replacements: dict[str, str]) -> str:
    """Replaces words in text based on a dictionary of replacements.

    Preserves the case of the original word: uppercase, title case, or lowercase.

    Args:
        text: The text within which to perform word swaps.
        replacements: A dictionary whose keys are the words to replace with their corresponding values.

    Returns:
        The updated text with words replaced as specified.
    """

    def _replacement_callable(match: re.Match) -> str:
        word = match.group(0)
        replacement = replacements[word.casefold()]  # Case-insensitive lookup
        return replacement.upper() if word.isupper() else replacement.capitalize() if word.istitle() else replacement

    # Compile regex pattern with case-insensitive matching for whole words
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, replacements)) + r")\b", re.IGNORECASE)

    return pattern.sub(_replacement_callable, text)
