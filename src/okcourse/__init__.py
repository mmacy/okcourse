import logging
from importlib.metadata import PackageNotFoundError, version

from .constants import AI_DISCLAIMER, MAX_LECTURES
from .generators import AsyncOpenAICourseGenerator, CourseGenerator
from .models import Course, CourseGenerationResult, CourseGeneratorSettings, CourseOutline, Lecture, LectureTopic
from .settings import default_generator_settings
from .utils import get_logger, get_duration_string_from_seconds, sanitize_filename, LLM_SMELLS

__all__ = [
    "AI_DISCLAIMER",
    "MAX_LECTURES",
    "AsyncOpenAICourseGenerator",
    "CourseGenerator",
    "Course",
    "CourseGenerationResult",
    "CourseGeneratorSettings",
    "CourseOutline",
    "Lecture",
    "LectureTopic",
    "default_generator_settings",
    "get_logger",
    "get_duration_string_from_seconds",
    "sanitize_filename",
    "LLM_SMELLS",
]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"


# Avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
