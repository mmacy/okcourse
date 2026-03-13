"""The `async_azure_openai` module contains the [`AzureOpenAIAsyncGenerator`][okcourse.AzureOpenAIAsyncGenerator] class.

Uses the Azure OpenAI v1 API with the standard `AsyncOpenAI` client, configured with a
`base_url` pointing to the Azure resource endpoint.

Requires the `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` environment variables,
or the corresponding constructor parameters.
"""

import os

from openai import AsyncOpenAI

from okcourse.generators.base import CourseGenerator
from okcourse.generators.openai.async_openai import OpenAIAsyncGenerator
from okcourse.models import Course


class AzureOpenAIAsyncGenerator(OpenAIAsyncGenerator):
    """Uses Azure OpenAI to generate course content asynchronously.

    This generator inherits all generation logic from
    [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator] and overrides only the client
    initialization to point at an Azure OpenAI resource using the v1 API.

    The `model` fields in [`CourseSettings`][okcourse.CourseSettings] (e.g.,
    `text_model_outline`, `text_model_lecture`, `image_model`, `tts_model`) must be set to
    Azure **deployment names** rather than OpenAI model IDs.

    Examples:

    ```python
    import asyncio
    from okcourse import Course, AzureOpenAIAsyncGenerator

    async def main():
        course = Course(title="Cloud Architecture Fundamentals")
        # Set deployment names (not model IDs)
        course.settings.text_model_outline = "my-gpt4-deployment"
        course.settings.text_model_lecture = "my-gpt4-deployment"
        course.settings.image_model = "my-dalle3-deployment"
        course.settings.tts_model = "my-tts-deployment"

        generator = AzureOpenAIAsyncGenerator(course)
        course = await generator.generate_outline(course)
        course = await generator.generate_lectures(course)

    asyncio.run(main())
    ```
    """

    def __init__(
        self,
        course: Course,
        azure_endpoint: str | None = None,
        api_key: str | None = None,
    ):
        """Initializes the asynchronous Azure OpenAI course generator.

        Args:
            course: The course to generate content for.
            azure_endpoint: The Azure OpenAI resource endpoint URL
                (e.g., ``https://my-resource.openai.azure.com``). Falls back to the
                ``AZURE_OPENAI_ENDPOINT`` environment variable if not provided.
            api_key: The Azure OpenAI API key. Falls back to the ``AZURE_OPENAI_API_KEY``
                environment variable if not provided.

        Raises:
            ValueError: If neither the parameter nor the environment variable is set for
                the endpoint or API key.
        """
        endpoint = azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise ValueError(
                "Azure OpenAI endpoint required. Set the AZURE_OPENAI_ENDPOINT "
                "environment variable or pass the azure_endpoint parameter."
            )

        key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "Azure OpenAI API key required. Set the AZURE_OPENAI_API_KEY "
                "environment variable or pass the api_key parameter."
            )

        # Normalize endpoint to the v1 API path
        base_url = endpoint.rstrip("/")
        if not base_url.endswith("/openai/v1"):
            base_url += "/openai/v1"

        # Call CourseGenerator.__init__ directly to set up logging, generator info,
        # and prompts without creating a default OpenAI client
        CourseGenerator.__init__(self, course)

        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=key,
        )
