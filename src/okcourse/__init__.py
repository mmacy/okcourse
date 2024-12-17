from importlib.metadata import PackageNotFoundError, version

from .models import Lecture, Course, CourseOutline, LectureTopic
from .okcourse import (
    generate_course_audio,
    generate_course,
    generate_course_outline,
    generate_course_text,
)
from .utils import get_duration_string_from_seconds

__all__ = [
    "generate_course_audio",
    "generate_course_outline",
    "generate_course_text",
    "get_duration_string_from_seconds",
    "Lecture",
    "Course",
    "CourseOutline",
    "LectureTopic",
    "generate_course",
    "sanitize_filename",
]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"
