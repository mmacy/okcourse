from importlib.metadata import PackageNotFoundError, version

from .constants import TTS_VOICES
from .models import Course, CourseOutline, Lecture, LectureTopic
from .okcourse import (
    generate_course,
    generate_course_async,
    generate_course_audio,
    generate_course_audio_async,
    generate_course_lectures,
    generate_course_lectures_async,
    generate_course_outline,
    generate_course_outline_async,
)
from .utils import get_duration_string_from_seconds, sanitize_filename

__all__ = [
    "Course",
    "CourseOutline",
    "Lecture",
    "LectureTopic",
    "TTS_VOICES",
    "generate_course_async",
    "generate_course_audio_async",
    "generate_course_audio",
    "generate_course_lectures_async",
    "generate_course_lectures",
    "generate_course_outline_async",
    "generate_course_outline",
    "generate_course",
    "get_duration_string_from_seconds",
    "sanitize_filename",
]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"
