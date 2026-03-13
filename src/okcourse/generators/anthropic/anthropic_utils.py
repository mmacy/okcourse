"""Shared utilities for interacting with the Anthropic API."""

from anthropic import AsyncAnthropic

from okcourse.utils.log_utils import get_logger

_log = get_logger(__name__)

# Fallback model list used when the API is unreachable or no API key is set
_FALLBACK_TEXT_MODELS: list[str] = [
    "claude-haiku-4-5-20251001",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
]

# Cache the available text models to avoid redundant API calls
_anthropic_text_models: list[str] | None = None


async def _get_anthropic_text_models(client: AsyncAnthropic) -> list[str]:
    """Fetches text models available from the Anthropic API.

    Args:
        client: The Anthropic async client to use for the API call.

    Returns:
        A sorted list of model ID strings for Claude text models.
    """
    models: list[str] = []
    try:
        _log.info("Fetching list of models from Anthropic API...")
        page = await client.models.list(limit=1000)
        for model_info in page.data:
            models.append(model_info.id)
        models.sort()
        _log.info(f"Got {len(models)} models from Anthropic API.")
    except Exception as e:
        _log.warning(f"Failed to fetch Anthropic models, using fallback list: {e}")
        return list(_FALLBACK_TEXT_MODELS)
    return models


async def get_anthropic_text_models_async() -> list[str]:
    """Gets the available Anthropic text models, fetching them if not already cached.

    Returns:
        A sorted list of Anthropic model ID strings.
    """
    global _anthropic_text_models
    if _anthropic_text_models is None:
        _anthropic_text_models = await _get_anthropic_text_models(AsyncAnthropic())
    return _anthropic_text_models
