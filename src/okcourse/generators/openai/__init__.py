"""OpenAI-based course generators that generate course assets using OpenAI's models.

An asynchronous generator. `OpenAIAsyncGenerator`, is ready for use. A synchronous generator, `OpenAISyncGenerator`, is
planned but not yet implemented.
"""

from .async_openai import OpenAIAsyncGenerator
# from .sync_openai import OpenAISyncGenerator  # NOT YET IMPLEMENTED

__all__ = [
    "OpenAIAsyncGenerator",
    # "OpenAISyncGenerator"  # NOT YET IMPLEMENTED
]
