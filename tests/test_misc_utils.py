"""Unit tests for okcourse misc utility functions."""

import pytest
from typing import Literal, Union, Optional

from okcourse.utils.misc_utils import (
    extract_literal_values_from_type,
    extract_literal_values_from_member
)


def test_extract_literal_values_from_simple_literal():
    """Test extracting values from a simple Literal type."""
    Voice = Literal["alloy", "echo", "fable"]
    values = extract_literal_values_from_type(Voice)
    assert sorted(values) == ["alloy", "echo", "fable"]


def test_extract_literal_values_from_union_with_literal():
    """Test extracting values from a Union containing Literal."""
    VoiceOrNone = Union[Literal["voice1", "voice2"], None]
    values = extract_literal_values_from_type(VoiceOrNone)
    assert sorted(values) == ["voice1", "voice2"]


def test_extract_literal_values_from_optional_literal():
    """Test extracting values from Optional[Literal[...]]."""
    OptionalVoice = Optional[Literal["option1", "option2"]]
    values = extract_literal_values_from_type(OptionalVoice)
    assert sorted(values) == ["option1", "option2"]


def test_extract_literal_values_from_nested_union():
    """Test extracting values from nested Union with multiple Literals."""
    ComplexType = Union[Literal["a", "b"], Literal["c", "d"], str]
    values = extract_literal_values_from_type(ComplexType)
    assert sorted(values) == ["a", "b", "c", "d"]


def test_extract_literal_values_from_non_literal_raises_error():
    """Test that extracting from non-Literal type raises TypeError."""
    with pytest.raises(TypeError, match="No Literal values found"):
        extract_literal_values_from_type(str)


def test_extract_literal_values_from_member():
    """Test extracting literal values from a class member."""
    class TestClass:
        voice: Literal["alloy", "echo", "fable"]
        model: str
    
    values = extract_literal_values_from_member(TestClass, "voice")
    assert sorted(values) == ["alloy", "echo", "fable"]


def test_extract_literal_values_from_member_with_union():
    """Test extracting literal values from a class member with Union."""
    class TestClass:
        voice: Union[Literal["voice1", "voice2"], None]
    
    values = extract_literal_values_from_member(TestClass, "voice")
    assert sorted(values) == ["voice1", "voice2"]


def test_extract_literal_values_from_member_missing_member():
    """Test that extracting from non-existent member raises AttributeError."""
    class TestClass:
        voice: Literal["alloy", "echo"]
    
    with pytest.raises(AttributeError, match="Member 'missing' not found"):
        extract_literal_values_from_member(TestClass, "missing")


def test_extract_literal_values_from_member_non_literal():
    """Test that extracting from non-Literal member raises TypeError."""
    class TestClass:
        voice: str
    
    with pytest.raises(TypeError, match="does not contain any Literal values"):
        extract_literal_values_from_member(TestClass, "voice")


def test_extract_literal_values_empty_literal():
    """Test behavior with empty Literal (edge case)."""
    # This is a bit of an edge case - empty Literal types are unusual
    # but we should handle them gracefully
    with pytest.raises(TypeError, match="No Literal values found"):
        extract_literal_values_from_type(Union[str, int])  # No literals here