"""The `generators` package includes course content generators compatible with APIs offered by different service providers.

Generators:
    - CourseGenerator: Base class for course generators.
    - OpenAIAsyncCourseGenerator: Asynchronous course generator for the OpenAI API.
    - OpenAISyncCourseGenerator: (NOT YET IMPLEMENTED) Synchronous course generator for the OpenAI API.
"""

from .base import CourseGenerator
from .openai.async_openai import AsyncOpenAICourseGenerator
# from .openai.openai import OpenAICourseGenerator

__all__ = [
    "CourseGenerator",
    "AsyncOpenAICourseGenerator",
    # "OpenAICourseGenerator",
]
