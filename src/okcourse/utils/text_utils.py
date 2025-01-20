"""String utilities for text processing and management in the `okcourse` package.

This module provides a collection of functions for processing strings and managing text, including tokenizer checks
and downloads, splitting text into chunks, sanitizing filenames, formatting durations, and swapping words to reduce
LLM-specific word inflections.

Examples of usage include:

- Checking and downloading an NLTK tokenizer:

  ```python
  from text_utils import tokenizer_available, download_tokenizer

  if not tokenizer_available():
      download_tokenizer()
  ```

- Splitting text into manageable chunks:

  ```python
  from text_utils import split_text_into_chunks

  text = "Your long text here..."
  chunks = split_text_into_chunks(text, max_chunk_size=1024)
  ```

- Sanitizing a name for use as a filename:

  ```python
  from text_utils import sanitize_filename

  safe_name = sanitize_filename("My Unsafe Filename.txt")
  ```

- Formatting a duration in seconds to a human-readable format:

  ```python
  from text_utils import get_duration_string_from_seconds

  duration = get_duration_string_from_seconds(3661)  # "1:01:01"
  ```

- Replacing overused LLM words with simpler alternatives:

  ```python
  from text_utils import swap_words, LLM_SMELLS

  updated_text = swap_words("In this course we delve into...", LLM_SMELLS)
  ```
"""

import re
from datetime import timedelta

import nltk

from .log_utils import get_logger

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
    """Splits text into chunks of approximately `max_chunk_size` characters, preserving sentence boundaries.

    If a sentence exceeds `max_chunk_size`, a ValueError is raised.

    Typical use of this function is to split a long piece of text into chunks that are each just under the character
    length limit a TTS model will accept for converting to audio. For example, OpenAI's `tts-1` model has a limit of
    4096 characters.

    Args:
        text: The text to split.
        max_chunk_size: The maximum number of characters in each chunk.

    Returns:
        A list of text chunks where each chunk is equal to or less than the `max_chunk_size`.

    Raises:
        ValueError: If `max_chunk_size` < 1 or if a sentence exceeds `max_chunk_size`.
    """
    if max_chunk_size < 1:
        raise ValueError("max_chunk_size must be greater than 0")

    sentences = nltk.sent_tokenize(text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)

        if sentence_length > max_chunk_size:
            # Cannot process this sentence; it's too long
            raise ValueError(
                f"Sentence length {sentence_length} exceeds max_chunk_size {max_chunk_size}. "
                "Cannot split sentence further without potentially altering its meaning."
            )

        if current_length + sentence_length + 1 <= max_chunk_size:
            # Sentence can fit in current chunk
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 accounts for space or punctuation
        else:
            # Sentence doesn't fit in the current chunk, so add the current chunk to the
            # chunks collection and start a new chunk with the sentence that didn't fit
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length

    # Add any "leftover" sentences in the current chunk to the chunks collection
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
    "crucial": "critical",
    # underscore
    # paramount
}
"""Dictionary mapping words overused by some large language models to their simplified 'everyday' forms.

Words in the keys may be replaced by their simplified forms in generated lecture text to help reduce \"LLM smell.\"

This dictionary is appropriate for use as the `replacements` parameter in the
[`swap_words`][okcourse.utils.text_utils.swap_words] function.
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
