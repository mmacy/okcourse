"""Utility for bundling course artifacts into an in-memory ZIP archive."""

from __future__ import annotations

import io
from zipfile import ZipFile, ZIP_DEFLATED
from dataclasses import dataclass
from typing import Optional


@dataclass
class InMemoryCoursePack:
    """Container for all course artifacts stored as a ZIP file in memory."""

    zip_bytes: bytes

    @classmethod
    def from_course(cls, course: "Course") -> "InMemoryCoursePack":
        """Create a zip of course JSON, image, and audio stored in memory."""
        buffer = io.BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as zf:
            zf.writestr("course.json", course.model_dump_json(indent=2))
            if course.generation_info.image_bytes:
                zf.writestr("cover.png", course.generation_info.image_bytes)
            if course.generation_info.audio_bytes:
                zf.writestr("audio.mp3", course.generation_info.audio_bytes)
        buffer.seek(0)
        return cls(zip_bytes=buffer.getvalue())

