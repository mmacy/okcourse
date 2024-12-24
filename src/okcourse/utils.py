import os
import logging
from datetime import timedelta

import nltk
import re


log = logging.getLogger(__name__)


def configure_logging(level: int | None = None):
    """Configure logging for the okcourse library.

    Args:
        level: Optional log level to override the default or environment variable.
               If not provided, uses the environment variable `OKCOURSE_LOG_LEVEL`
               or defaults to `INFO`.
    """
    if level is None:  # Use environment variable if no level is explicitly provided
        env_level = os.getenv("OKCOURSE_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s][%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Configure loggers for the okcourse library
    for logger_name in ["okcourse", "okcourse.utils", "okcourse.models"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.addHandler(console_handler)
        logger.propagate = False  # Prevents messages from propagating to the root logger


def tokenizer_available() -> bool:
    """Checks if the NLTK 'punkt_tab' tokenizer is available on the system.

    Returns:
        True if the tokenizer is available.
    """
    try:
        log.info("Checking for NLTK 'punkt_tab' tokenizer...")
        nltk.data.find("tokenizers/punkt_tab")
        log.info("Found NLTK 'punkt_tab' tokenizer.")
        return True
    except LookupError:
        log.warning("NLTK 'punkt_tab' tokenizer NOT found. Download it with ``download_tokenizer()``.")
        return False


def download_tokenizer() -> bool:
    """Downloads the NLTK 'punkt_tab' tokenizer.

    Returns:
        True if the tokenizer was downloaded.
    """
    try:
        log.info("Downloading NLTK 'punkt_tab' tokenizer...")
        nltk.download("punkt_tab", raise_on_error=True)
        log.info("Downloaded NLTK 'punkt_tab' tokenizer.")
        return True
    except Exception as e:
        log.error(f"Error downloading NLTK 'punkt_tab' tokenizer: {e}")
        return False


def split_text_into_chunks(text: str, max_chunk_size: int = 4096) -> list[str]:
    """Splits text into chunks of approximately `max_chunk_size` characters.

    The first time you call this function, it will check the default download location for the NLTK 'punkt_tab' tokenizer.
    If the tokenizer is not found, it will attempt to download it. Subsequent calls will not re-download the tokenizer.

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
