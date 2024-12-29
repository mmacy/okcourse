"""The `okcourse` package provides a lightweight interface for Python applications to use AI models to generate
audiobook-style courses containing lectures on any topic.

Given a course title, a [course generator][okcourse.generators] will:

- Generate a [course outline][okcourse.generators.base.CourseGenerator.generate_outline] for the course.
- Generate [lecture text][okcourse.generators.base.CourseGenerator.generate_lectures] for each topic in the outline.
- Generate a [cover image][okcourse.generators.base.CourseGenerator.generate_image] for the audio file "album" art.
- Generate an [audio file][okcourse.generators.base.CourseGenerator.generate_audio] text-to-speech model to
   to produce audio from the lecture text.

The `okcourse` library includes a [generator base class][okcourse.generators.base.CourseGenerator] that defines the
methods required by implementing subclasses to perform the course generation tasks.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

from .generators import OpenAIAsyncGenerator
from .models import Course, CourseGenerationResult, CourseGeneratorSettings, CourseOutline, Lecture, LectureTopic

__all__ = [
    "Course",
    "CourseGenerationResult",
    "CourseGeneratorSettings",
    "CourseOutline",
    "Lecture",
    "LectureTopic",
    "OpenAIAsyncGenerator",
]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"


# Avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
