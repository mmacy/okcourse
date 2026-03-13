"""Tests for AzureOpenAIAsyncGenerator."""

import os
from unittest.mock import patch

import pytest

from okcourse import AzureOpenAIAsyncGenerator, Course
from okcourse.generators.openai.async_openai import OpenAIAsyncGenerator


@pytest.fixture
def course() -> Course:
    """Return a minimal Course for testing."""
    return Course(title="Test Course")


class TestAzureOpenAIInit:
    """Tests for AzureOpenAIAsyncGenerator constructor."""

    def test_raises_without_endpoint(self, course: Course) -> None:
        """Constructor raises ValueError when no endpoint is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Azure OpenAI endpoint required"):
                AzureOpenAIAsyncGenerator(course, api_key="fake-key")

    def test_raises_without_api_key(self, course: Course) -> None:
        """Constructor raises ValueError when no API key is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Azure OpenAI API key required"):
                AzureOpenAIAsyncGenerator(
                    course, azure_endpoint="https://my-resource.openai.azure.com"
                )

    def test_accepts_constructor_params(self, course: Course) -> None:
        """Constructor succeeds with explicit parameters."""
        gen = AzureOpenAIAsyncGenerator(
            course,
            azure_endpoint="https://my-resource.openai.azure.com",
            api_key="fake-key",
        )
        assert gen.client is not None
        assert str(gen.client.base_url).rstrip("/").endswith("/openai/v1")

    def test_accepts_env_vars(self, course: Course) -> None:
        """Constructor succeeds with environment variables."""
        env = {
            "AZURE_OPENAI_ENDPOINT": "https://my-resource.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "fake-key",
        }
        with patch.dict(os.environ, env, clear=False):
            gen = AzureOpenAIAsyncGenerator(course)
            assert gen.client is not None

    def test_constructor_params_override_env_vars(self, course: Course) -> None:
        """Constructor parameters take precedence over environment variables."""
        env = {
            "AZURE_OPENAI_ENDPOINT": "https://env-resource.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "env-key",
        }
        with patch.dict(os.environ, env, clear=False):
            gen = AzureOpenAIAsyncGenerator(
                course,
                azure_endpoint="https://param-resource.openai.azure.com",
                api_key="param-key",
            )
            assert "param-resource" in str(gen.client.base_url)
            assert gen.client.api_key == "param-key"


class TestAzureOpenAIEndpointNormalization:
    """Tests for endpoint URL normalization."""

    @pytest.mark.parametrize(
        "endpoint,expected_suffix",
        [
            ("https://res.openai.azure.com", "/openai/v1"),
            ("https://res.openai.azure.com/", "/openai/v1"),
            ("https://res.openai.azure.com/openai/v1", "/openai/v1"),
            ("https://res.openai.azure.com/openai/v1/", "/openai/v1"),
        ],
    )
    def test_normalizes_endpoint(self, course: Course, endpoint: str, expected_suffix: str) -> None:
        """Endpoint is normalized to include /openai/v1 path."""
        gen = AzureOpenAIAsyncGenerator(course, azure_endpoint=endpoint, api_key="fake-key")
        base_url = str(gen.client.base_url).rstrip("/")
        assert base_url.endswith(expected_suffix)


class TestAzureOpenAIInheritance:
    """Tests for correct inheritance from OpenAIAsyncGenerator."""

    def test_is_subclass_of_openai_generator(self) -> None:
        """AzureOpenAIAsyncGenerator is a subclass of OpenAIAsyncGenerator."""
        assert issubclass(AzureOpenAIAsyncGenerator, OpenAIAsyncGenerator)

    def test_instance_is_openai_generator(self, course: Course) -> None:
        """An instance is also an instance of OpenAIAsyncGenerator."""
        gen = AzureOpenAIAsyncGenerator(
            course,
            azure_endpoint="https://res.openai.azure.com",
            api_key="fake-key",
        )
        assert isinstance(gen, OpenAIAsyncGenerator)

    def test_generator_type_recorded(self, course: Course) -> None:
        """The generator type in generation_info reflects the Azure subclass."""
        gen = AzureOpenAIAsyncGenerator(
            course,
            azure_endpoint="https://res.openai.azure.com",
            api_key="fake-key",
        )
        assert "AzureOpenAIAsyncGenerator" in course.generation_info.generator_type

    def test_inherits_generate_methods(self, course: Course) -> None:
        """All four generate_* methods are inherited (not overridden)."""
        gen = AzureOpenAIAsyncGenerator(
            course,
            azure_endpoint="https://res.openai.azure.com",
            api_key="fake-key",
        )
        for method_name in ("generate_outline", "generate_lectures", "generate_image", "generate_audio"):
            method = getattr(gen, method_name)
            # The method should be bound and come from OpenAIAsyncGenerator
            assert callable(method)
            assert method_name not in AzureOpenAIAsyncGenerator.__dict__
