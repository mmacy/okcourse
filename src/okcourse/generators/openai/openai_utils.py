"""Shared utilities for interacting with the OpenAI API."""

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

from openai import AsyncOpenAI, RateLimitError
from openai.types import Model
from openai.types.audio.speech_create_params import SpeechCreateParams
from openai.types.audio.speech_model import SpeechModel
from openai.types.chat_model import ChatModel
from openai.types.image_model import ImageModel

from okcourse.utils.log_utils import get_logger
from okcourse.utils.misc_utils import extract_literal_values_from_member, extract_literal_values_from_type

_log = get_logger(__name__)

tts_voices: list[str] = extract_literal_values_from_member(SpeechCreateParams, "voice")


@dataclass
class AIModels:
    """The AI models available for use by an OpenAI client, grouped by type."""
    image_models: list[str]
    """Image generation or manipulation models."""
    speech_models: list[str]
    """Text-to-speech models."""
    text_models: list[str]
    """Text completion models."""
    other_models: list[str] | None
    """All other model types."""


def _get_all_models_known_to_library() -> AIModels:
    """Gets all the models known to the OpenAI Python library.

    These are *all* the available models the OpenAI library knows about, which might include models not available for
    use by the client's API key. Not included are any custom models (typically fine-tuned models) in the account
    represented by the API key.

    Returns:
        AIModels: All models known to the OpenAI Python library. Excludes custom (user-created) models.
    """

    return


async def _get_usable_models(openai_client: AsyncOpenAI) -> AIModels:
    """Gets lists of models by model type available for use by the client.

    Not all models are available for use by all clients. Availability is based on the pemissions granted by the OpenAI
    API key used when instantiating client.

    Args:
        openai_client: The OpenAI client to use for fetching the list of models from the API.

    Returns:
        AIModels:  All models available for use by the client.
    """

    image_models: list[str] = []
    text_models: list[str] = []
    speech_models: list[str] = []
    other_models: list[str] = []

    # These are all the models known to the OpenAI library, which might be a subset of those available for use
    # by the client. We use this set of models to categorize the usable models list returned by the API.
    all_known_models = AIModels(
        image_models=extract_literal_values_from_type(ImageModel),
        speech_models=extract_literal_values_from_type(SpeechModel),
        text_models=extract_literal_values_from_type(ChatModel),
        other_models=[],
    )

    # The flat list of models returned by the OpenAI API that are available for use by the client
    usable_models_list: list[Model] = []

    # The models grouped by type that the client can use
    usable_models: AIModels = None

    try:
        _log.info("Fetching list of models available for use by current API key...")
        usable_models_list = await openai_client.models.list()
        _log.info(f"Got {len(usable_models_list.data)} models from OpenAI API.")
    except Exception as e:
        _log.error(f"Failed to fetch models: {e}")
        raise e

    # Categorize models based on the extracted literals
    usable_models_list.data.sort(key=lambda model: (-model.created, model.id))
    for model in usable_models_list.data:
        if model.id in all_known_models.text_models:
            text_models.append(model.id)
        elif model.id in all_known_models.image_models:
            image_models.append(model.id)
        elif model.id in all_known_models.speech_models:
            speech_models.append(model.id)
        else:
            other_models.append(model.id)

    usable_models = AIModels(
        image_models=image_models,
        text_models=text_models,
        speech_models=speech_models,
        other_models=other_models,
    )

    return usable_models


# Cache the available models to avoid redundant API calls
_usable_models: AIModels | None = None


async def get_usable_models_async() -> AIModels:
    """Asynchronously get the usable models, fetching them if not already cached."""
    global _usable_models
    if _usable_models is None:
        _usable_models = await _get_usable_models(AsyncOpenAI())
    return _usable_models


def get_usable_models_sync() -> AIModels:
    """Synchronously get the usable models using asyncio.run()."""
    return asyncio.run(get_usable_models_async())


def _get_retry_after(error: RateLimitError) -> int | None:
    """Extracts the `retry-after-ms` value from the response headers of the given RateLimitError.

    Args:
        error: The exception containing the response and headers.

    Returns:
        The retry-after value in seconds, or None if unavailable.
    """
    try:
        # Access headers from the response embedded in the error
        retry_after = error.response.headers.get("retry-after-ms")
        if retry_after:
            return int(retry_after)
    except (AttributeError, ValueError):
        # Handle cases where headers are missing or value is not an integer
        pass
    return None


T = TypeVar("T")


async def execute_request_with_retry(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    max_retries: int = 6,
    initial_delay_ms: float = 1000,
    exponential_base: float = 2,
    jitter: bool = True,
    **kwargs: Any,
) -> T:
    """Calls an async function and retries with exponential backoff on RateLimitError.

    This method parses the rate-limit-specific wait time from the OpenAI error and uses random exponential backoff to
    avoid hammering the API in tight loops.

    Args:
        func: The function to call.
        *args: Positional arguments to pass to the function.
        max_retries: The maximum number of retries before giving up.
        initial_delay_ms: The initial delay in milliseconds before the first retry.
        exponential_base: The exponential growth factor for delay intervals.
        jitter: Whether to apply random jitter to the delay interval.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The awaited result of `func`.

    Raises:
        Exception: If `max_retries` is exceeded.
    """
    attempt = 0
    delay_ms = initial_delay_ms

    while True:
        try:
            return await func(*args, **kwargs)
        except RateLimitError as rle:
            _log.warning(f"RateLimitError hit: {rle}")

            attempt += 1
            if attempt > max_retries:
                raise Exception(f"Max retries ({max_retries}) exceeded.") from rle

            # Parse recommended wait time from the error, fall back to existing delay if smaller
            retry_after_milliseconds = _get_retry_after(rle)
            delay_ms = max(delay_ms, retry_after_milliseconds)
            # Add exponential backoff
            if jitter:
                # Multiply delay by random factor in [1, 2) to spread out bursts
                delay_ms *= exponential_base * (1 + random.random()) / 1000
            else:
                delay_ms *= exponential_base / 1000

            _log.warning(f"Will retry in {round(delay_ms, 2)} seconds (attempt {attempt}/{max_retries})...")
            await asyncio.sleep(delay_ms)
