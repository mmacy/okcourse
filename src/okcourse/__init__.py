from importlib.metadata import PackageNotFoundError, version

from .models import Lecture, LectureSeries, LectureSeriesOutline, LectureTopic
from .okcourse import (
    generate_audio_for_lectures_in_series,
    generate_complete_lecture_series,
    generate_lecture_series_outline,
    generate_text_for_lectures_in_series,
)
from .utils import get_duration_string_from_seconds

__all__ = [
    "generate_audio_for_lectures_in_series",
    "generate_lecture_series_outline",
    "generate_text_for_lectures_in_series",
    "get_duration_string_from_seconds",
    "Lecture",
    "LectureSeries",
    "LectureSeriesOutline",
    "LectureTopic",
    "generate_complete_lecture_series",
    "sanitize_filename",
]

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = "unknown"
