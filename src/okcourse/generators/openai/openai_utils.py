"""Shared utilities for interacting with the OpenAI API."""

import asyncio
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI

from openai.types.audio.speech_create_params import SpeechCreateParams
from openai.types.audio.speech_model import SpeechModel
from openai.types.chat_model import ChatModel
from openai.types.image_model import ImageModel
from openai.types import Model

from okcourse.utils.log_utils import get_logger
from okcourse.utils.misc_utils import extract_literal_values_from_member, extract_literal_values_from_type


client = AsyncOpenAI()

_log = get_logger(__name__)

tts_voices: list[str] = extract_literal_values_from_member(SpeechCreateParams, "voice")


@dataclass
class AIModels:
    image_models: list[str]
    speech_models: list[str]
    text_models: list[str]
    other_models: list[str] | None


def _get_library_models() -> AIModels:
    """Gets all the models known to the OpenAI Python library.

    These are *all* the available models the OpenAI library knows about, which might include models not available for
    use by the client's API key. Not included are any custom models (typically fine-tuned models) in the account
    represented by the API key.

    Returns:
        AIModels: All models known to the OpenAI Python library. Excludes custom (user-created) models.
    """

    return AIModels(
        image_models=extract_literal_values_from_type(ImageModel),
        speech_models=extract_literal_values_from_type(SpeechModel),
        text_models=extract_literal_values_from_type(ChatModel),
        other_models=[],
    )


async def _get_usable_models() -> AIModels:
    """Gets the models available for use from the OpenAI API for the API key in use by the client.

    Returns:
        AIModels: _description_
    """

    # Initialize lists to store the categorized model IDs
    image_models: list[str] = []
    text_models: list[str] = []
    speech_models: list[str] = []
    other_models: list[str] = []

    all_models = _get_library_models()

    try:
        _log.info("Fetching list of models available for use by current API key...")
        models_list: list[Model] = await client.models.list()
        _log.info(f"Got {len(models_list.data)} models from OpenAI API.")
    except Exception as e:
        _log.error(f"Failed to fetch models: {e}")
        raise e

    # Categorize models based on the extracted literals
    models_list.data.sort(key=lambda model: (-model.created, model.id))
    for model in models_list.data:
        if model.id in all_models.text_models:
            text_models.append(model.id)
        elif model.id in all_models.image_models:
            image_models.append(model.id)
        elif model.id in all_models.speech_models:
            speech_models.append(model.id)
        else:
            other_models.append(model.id)

    return AIModels(
        image_models=image_models,
        text_models=text_models,
        speech_models=speech_models,
        other_models=other_models,
    )


# Cache the available models to avoid redundant API calls
_usable_models: Optional[AIModels] = None


async def get_usable_models_async() -> AIModels:
    """Asynchronously get the usable models, fetching them if not already cached."""
    global _usable_models
    if _usable_models is None:
        _usable_models = await _get_usable_models()
    return _usable_models


def get_usable_models_sync() -> AIModels:
    """Synchronously get the usable models using asyncio.run()."""
    return asyncio.run(get_usable_models_async())
