"""Pydantic model classes representing a course and its outline, lectures, and generated output."""

from pathlib import Path

from pydantic import BaseModel, Field

from .settings import CourseGeneratorSettings


class LectureTopic(BaseModel):
    number: int = Field(..., description="The position number of the lecture within the series.")
    title: str = Field(..., description="The topic of a lecture within a course.")
    subtopics: list[str] = Field(..., description="The subtopics covered in the lecture.")

    def __str__(self) -> str:
        subtopics_str = "\n".join(f"  - {sub}" for sub in self.subtopics) if self.subtopics else ""
        return f"Lecture {self.number}: {self.title}\n{subtopics_str}"


class CourseOutline(BaseModel):
    title: str = Field(..., description="The title of the course.")
    topics: list[LectureTopic] = Field(..., description="The topics covered by each lecture in the series.")

    def __str__(self) -> str:
        topics_str = "\n\n".join(str(topic) for topic in self.topics)
        return f"Course title: {self.title}\n\n{topics_str}"


class Lecture(LectureTopic):
    text: str = Field(..., description="The unabridged text content of the lecture.")

    def __str__(self) -> str:
        return f"{self.title}\n\n{self.text}"


class Course(BaseModel):
    outline: CourseOutline = Field(..., description="The detailed outline of the course.")
    lectures: list[Lecture] | None = Field(None, description="The lectures that comprise the complete course.")

    def __str__(self) -> str:
        if not self.lectures:
            return str(self.outline)
        lectures_str = "\n\n".join(str(lecture) for lecture in self.lectures)
        return f"{self.outline}\n\n{lectures_str}"

    @property
    def title(self) -> str:
        return self.outline.title


class CourseGenerationResult(BaseModel):
    settings: CourseGeneratorSettings | None = Field(
        None, description="The settings used to generate the course assets."
    )
    course: Course | None = Field(
        None, description="The generated course model or `None` if the course has yet to be generated."
    )
    course_file_path: Path | None = Field(None, description="The path to the JSON file containing the course content.")
    audio_file_path: Path | None = Field(
        None, description="The path to the audio file generated from the course content."
    )
    image_file_path: Path | None = Field(None, description="The path to the cover image generated for the course.")
