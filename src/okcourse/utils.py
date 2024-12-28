"""Utility functions that support operations performed by other modules in the okcourse library."""

import logging
import re
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

import nltk


def get_logger(
    source_name: str = "okcourse", level: int = logging.INFO, file_path: Path | None = None
) -> logging.Logger:
    """Enable logging to the console and optionally to a file for the specified source.

    You typically will get the name of the source module or function by calling `__name__` in the source.

    Args:
        source_name: The source (module, method, etc.) that will pass log event messages to this logger.
        level: The logging level to set for the logger.
        file_path: The path to a file where logs will be written. If not provided, logs are written only to the console.
    """
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s][%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # The first call to getLogger() with a new source name creates a new logger instance for that source
    logger = logging.getLogger(source_name)
    logger.setLevel(level)
    # logger.propagate = False  # Prevents messages from propagating to the root logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if file_path:
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)
        file_handler = logging.FileHandler(str(file_path))
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Logger for this module
_log = get_logger(__name__)


def tokenizer_available() -> bool:
    """Checks if the NLTK 'punkt_tab' tokenizer is available on the system.

    Returns:
        True if the tokenizer is available.
    """
    try:
        _log.info("Checking for NLTK 'punkt_tab' tokenizer...")
        nltk.data.find("tokenizers/punkt_tab")
        _log.info("Found NLTK 'punkt_tab' tokenizer.")
        return True
    except LookupError:
        _log.warning("NLTK 'punkt_tab' tokenizer NOT found. Download it with ``download_tokenizer()``.")
        return False


def download_tokenizer() -> bool:
    """Downloads the NLTK 'punkt_tab' tokenizer.

    Returns:
        True if the tokenizer was downloaded.
    """
    try:
        _log.info("Downloading NLTK 'punkt_tab' tokenizer...")
        nltk.download("punkt_tab", raise_on_error=True)
        _log.info("Downloaded NLTK 'punkt_tab' tokenizer.")
        return True
    except Exception as e:
        _log.error(f"Error downloading NLTK 'punkt_tab' tokenizer: {e}")
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

    _log.info(f"Split text into {len(chunks)} chunks of ~{max_chunk_size} characters from {len(sentences)} sentences.")
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


LLM_SMELLS: dict[str, str] = {
    # "crucial": "important",  # TODO: Uncomment when we can handle phrases (currently breaks due to a/an mismatch).
    "delve": "dig",
    "delved": "dug",
    "delves": "digs",
    "delving": "digging",
    "utilize": "use",
    "utilized": "used",
    "utilizing": "using",
    "utilization": "usage",
    "meticulous": "careful",
    "meticulously": "carefully",
}
"""Dictionary mapping words overused by some large language models to their simplified 'everyday' forms.

Words in the keys may be replaced by their simplified forms in generated lecture text to help reduce \"LLM smell.\"

This dictionary is appropriate for use as the `replacements` parameter in the `swap_words` function.
"""


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


def extract_literal_values_from_type(typ: object) -> list[str]:
    """Unwraps a `typing.Literal[...]` or any nested `Union` containing `Literal`s and returns the literal values."""

    def unwrap_literal(t: object):
        origin = get_origin(t)
        if origin is Literal:
            yield from get_args(t)
        elif origin is Union:
            for arg in get_args(t):
                yield from unwrap_literal(arg)
        # If there's some other generic type, we could check for __args__ as needed,
        # but we typically only need Union and Literal.

    literals = list(unwrap_literal(typ))
    if not literals:
        raise TypeError("No Literal values found.")
    return literals


def extract_literal_values_from_member(cls: Any, member: str) -> list[Any]:
    """Extracts the `Literal` values of a specified member in a `class` or `TypedDict`.

    If the member's type is a `Literal` or contains Literals within a `Union` like `Optional[Literal[...]]`, the
    function extracts and returns all the `Literal` values.
    """
    type_hints = get_type_hints(cls)

    if member not in type_hints:
        raise AttributeError(f"Member '{member}' not found in type hints of {cls.__name__}.")

    member_type = type_hints[member]

    def unwrap_literal(t) -> list[Any]:
        literals = []
        origin = getattr(t, "__origin__", None)
        if origin is Literal:
            literals.extend(get_args(t))
        elif origin is Union:
            for arg in get_args(t):
                literals.extend(unwrap_literal(arg))
        return literals

    extracted_literals = unwrap_literal(member_type)
    if not extracted_literals:
        raise TypeError(f"Member '{member}' in {cls.__name__} does not contain any Literal values.")

    return extracted_literals
