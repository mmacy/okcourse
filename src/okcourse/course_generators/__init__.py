"""The `course_generators` package includes course content generators compatible with APIs offered by different service providers.

Generators:
    - CourseGenerator: Base class for course generators.
    - OpenAIAsyncCourseGenerator: Asynchronous course generator for the OpenAI API.
    - OpenAISyncCourseGenerator: Synchronous course generator for the OpenAI API.
"""

from .base import CourseGenerator
from .openai_generators import AsyncOpenAICourseGenerator

__all__ = [
    "CourseGenerator",
    "AsyncOpenAICourseGenerator",
]
