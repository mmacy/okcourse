"""The `okcourse` package provides a lightweight interface for Python applications to use AI models to generate
audiobook-style courses containing lectures on any topic.

Given a course title, a course generator like the [`OpenAIAsyncCourseGenerator`][okcourse.OpenAIAsyncGenerator] will fetch the following from an AI service provider's
API:

- [Course outline][okcourse.CourseOutline]
- [Lecture text][okcourse.Lecture] for the topics in the outline
- [Cover image][okcourse.CourseGenerator.generate_image] for the audio file album art
- [Audio file][okcourse.generators.base.CourseGenerator.generate_audio] from the lecture text
"""

import logging

from .generators import CourseGenerator, OpenAIAsyncGenerator
from .models import (
    Course,
    CourseGenerationInfo,
    CourseOutline,
    CourseSettings,
    Lecture,
    LectureTopic,
)

__all__ = [
    "Course",
    "CourseGenerationInfo",
    "CourseGenerator",
    "CourseOutline",
    "CourseSettings",
    "Lecture",
    "LectureTopic",
    "OpenAIAsyncGenerator",
]

# Avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
