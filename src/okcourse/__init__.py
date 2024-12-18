from importlib.metadata import PackageNotFoundError, version

from .constants import TTS_VOICES
from .models import Course, CourseOutline, Lecture, LectureTopic
from .okcourse import (
    generate_course,
    generate_course_audio,
    generate_course_lectures,
    generate_course_outline,
)
from .utils import get_duration_string_from_seconds, sanitize_filename

__all__ = [
    "generate_course_audio",
    "generate_course_outline",
    "generate_course_lectures",
    "get_duration_string_from_seconds",
    "Lecture",
    "Course",
    "CourseOutline",
    "LectureTopic",
    "generate_course",
    "sanitize_filename",
    "TTS_VOICES",
]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"
