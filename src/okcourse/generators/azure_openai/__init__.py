"""Course generators that use Azure OpenAI to produce courses and their assets."""

from .async_azure_openai import AzureOpenAIAsyncGenerator

__all__ = [
    "AzureOpenAIAsyncGenerator",
]
