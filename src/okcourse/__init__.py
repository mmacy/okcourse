import logging
from importlib.metadata import PackageNotFoundError, version

from .constants import *
from .models import Course, CourseOutline, Lecture, LectureTopic, CourseGeneratorSettings, CourseGenerationResult
from .okcourse import (
    AsyncOpenAICourseGenerator,
)
from .utils import enable_logging, get_duration_string_from_seconds, sanitize_filename

__all__ = [
    "AI_DISCLAIMER",
    "Course",
    "CourseGeneratorSettings",
    "CourseGenerationResult",
    "CourseOutline",
    "DEFAULT_IMAGE_MODEL",
    "DEFAULT_IMAGE_PROMPT",
    "DEFAULT_SYSTEM_PROMPT",
    "DEFAULT_TEXT_MODEL",
    "DEFAULT_TTS_MODEL",
    "LLM_SMELLS",
    "Lecture",
    "LectureTopic",
    "MAX_LECTURES",
    "TTS_VOICES",
    "enable_logging",
    "get_duration_string_from_seconds",
    "sanitize_filename",
]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"


# Avoid "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
