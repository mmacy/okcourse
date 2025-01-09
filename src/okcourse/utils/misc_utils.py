"""Miscellaneous utility functions that support operations performed by other modules in the okcourse library."""
from typing import (
    Any,
    Literal,
    Union,
    get_args,
    get_origin,
    get_type_hints
)


def extract_literal_values_from_type(typ: object) -> list[str]:
    """Unwraps a [`Literal`][typing.Literal] or any nested [`Union`][typing.Union] containing literals and returns the `Literal` values.

    An example use case for this function is to extract a list of the available voices from an OpenAI library type.
    """

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
    """Extracts the [`Literal`][typing.Literal] values of a specified member in a class or [`TypedDict`][typing.TypedDict].

    If the member's type is a `Literal` or contains literals within a [`Union`][typing.Union] like
    `Optional[Literal[...]]`, the function extracts and returns all the `Literal` values.

    An example use case for this function is to extract a list of the available models from an OpenAI library type.
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
