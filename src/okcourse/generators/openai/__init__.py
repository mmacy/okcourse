"""Course generators that use the OpenAI API to produce courses and their assets."""

from .async_openai import OpenAIAsyncGenerator
# from .sync_openai import OpenAISyncGenerator  # NOT YET IMPLEMENTED
from okcourse.generators.openai.openai_utils import AIModels, get_usable_models_sync, get_usable_models_async

__all__ = [
    "OpenAIAsyncGenerator",
    # "OpenAISyncGenerator"  # NOT YET IMPLEMENTED
    "AIModels",
    "get_usable_models_async",
    "get_usable_models_sync",
]
