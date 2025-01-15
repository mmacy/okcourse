from collections.abc import Sequence

import nltk
import pytest

from okcourse.utils.text_utils import split_text_into_chunks


@pytest.fixture(scope="session", autouse=True)
def nltk_setup() -> None:
    """Ensure that necessary NLTK data is downloaded before tests run."""
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)


@pytest.fixture
def short_text() -> str:
    """Return a short text string for testing."""
    return "This is a simple test sentence."


@pytest.fixture
def multi_sentence_text() -> str:
    """Return a text with multiple sentences for testing."""
    return "First sentence is here. Second sentence comes after. Third one is the last."


def test_split_text_into_chunks_short_text(short_text: str) -> None:
    """Test splitting text shorter than max chunk size.

    The text should not be split and should return as a single chunk.
    """
    chunks = split_text_into_chunks(short_text, max_chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text


def test_split_text_into_chunks_multiple_chunks(multi_sentence_text: str) -> None:
    """Test splitting text into multiple chunks.

    The text should be split into multiple chunks, each within the max_chunk_size.
    """
    max_chunk_size = 50
    chunks = split_text_into_chunks(multi_sentence_text, max_chunk_size=max_chunk_size)
    assert len(chunks) > 1
    assert all(len(chunk) <= max_chunk_size for chunk in chunks)


def test_split_text_into_chunks_preserves_sentences(multi_sentence_text: str) -> None:
    """Test that sentence boundaries are preserved in chunks.

    Ensures that sentences are not split between chunks.
    """
    chunks = split_text_into_chunks(multi_sentence_text, max_chunk_size=60)
    # Tokenize original sentences
    original_sentences = nltk.sent_tokenize(multi_sentence_text)
    # Tokenize sentences from chunks
    chunk_sentences: list[str] = []
    for chunk in chunks:
        chunk_sentences.extend(nltk.sent_tokenize(chunk))
    # Assert that the sentences are the same
    assert original_sentences == chunk_sentences


def test_split_text_into_chunks_empty_input() -> None:
    """Test behavior with empty input text.

    Expect an empty list of chunks.
    """
    chunks = split_text_into_chunks("", max_chunk_size=100)
    assert len(chunks) == 0


def test_split_text_into_chunks_invalid_chunk_size() -> None:
    """Test that invalid chunk sizes raise ValueError."""
    with pytest.raises(ValueError, match="max_chunk_size must be greater than 0"):
        split_text_into_chunks("Any text", max_chunk_size=0)
    with pytest.raises(ValueError, match="max_chunk_size must be greater than 0"):
        split_text_into_chunks("Any text", max_chunk_size=-1)


def test_split_text_into_chunks_small_chunk_size(multi_sentence_text: str) -> None:
    """Test behavior with very small chunk size."""
    chunks = split_text_into_chunks(multi_sentence_text, max_chunk_size=30)
    assert len(chunks) > 2
    assert all(len(chunk) <= 30 for chunk in chunks)


@pytest.mark.parametrize(
    "test_input, max_size, expected_chunks, expect_error",
    [
        # Simple single sentence within max_size
        ("One.", 10, ["One."], False),
        # Two short sentences that fit within max_size
        ("One. Two.", 10, ["One. Two."], False),
        # Multiple sentences with size constraint, sentences within max_size
        ("Short one. Another short one.", 20, ["Short one.", "Another short one."], False),
        # Test exact size match
        ("Test.", 5, ["Test."], False),
        # Test splitting on sentence boundary
        ("First. Second. Third.", 12, ["First.", "Second.", "Third."], False),
        # Sentence exceeds max_size, should raise ValueError
        ("A longer sentence here. Short one.", 20, None, True),
        # Sentence that is exactly max_size
        ("A" * 20, 20, ["A" * 20], False),
        # Another test case with sentence exceeding max_size
        ("A sentence that is definitely longer than twenty characters.", 20, None, True),
    ],
)
def test_split_text_into_chunks_various_inputs(
    test_input: str,
    max_size: int,
    expected_chunks: Sequence[str] | None,
    expect_error: bool,
) -> None:
    """Test splitting text with various inputs and expected outputs."""
    if expect_error:
        with pytest.raises(ValueError, match=r"Sentence length \d+ exceeds max_chunk_size \d+"):
            split_text_into_chunks(test_input, max_chunk_size=max_size)
    else:
        chunks = split_text_into_chunks(test_input, max_chunk_size=max_size)
        assert chunks == expected_chunks


def test_split_text_sentence_exceeds_max_chunk_size() -> None:
    """Test behavior when a sentence exceeds the max_chunk_size.

    A ValueError should be raised in this case.
    """
    long_sentence = "A" * 5000  # A very long sentence
    short_sentence = "This is a short sentence."
    text = f"{long_sentence} {short_sentence}"
    max_chunk_size = 1000

    # Expect a ValueError because the long sentence exceeds max_chunk_size
    with pytest.raises(ValueError, match=r"Sentence length \d+ exceeds max_chunk_size \d+"):
        split_text_into_chunks(text, max_chunk_size=max_chunk_size)


def test_split_text_sentence_equals_max_chunk_size() -> None:
    """Test behavior when a sentence is exactly max_chunk_size characters long.

    The sentence should be included in the chunks without error.
    """
    sentence_length = 100
    long_sentence = "A" * sentence_length  # A sentence exactly at max_chunk_size
    max_chunk_size = sentence_length

    chunks = split_text_into_chunks(long_sentence, max_chunk_size=max_chunk_size)
    assert len(chunks) == 1
    assert chunks[0] == long_sentence


def test_split_text_unicode_characters() -> None:
    """Test splitting text with Unicode characters.

    Ensures that texts with Unicode characters are split correctly.
    """
    text = "Voici la première phrase. C'est la deuxième phrase. Et enfin, la troisième."
    max_chunk_size = 40
    chunks = split_text_into_chunks(text, max_chunk_size=max_chunk_size)
    assert len(chunks) > 1
    assert all(len(chunk) <= max_chunk_size for chunk in chunks)
    # Verify that sentences are preserved
    original_sentences = nltk.sent_tokenize(text)
    chunk_sentences: list[str] = []
    for chunk in chunks:
        chunk_sentences.extend(nltk.sent_tokenize(chunk))
    assert original_sentences == chunk_sentences
