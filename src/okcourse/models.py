"""[Pydantic v2](https://docs.pydantic.dev/) models representing a course and its outline, lectures, and generated output."""

from pathlib import Path

from pydantic import BaseModel, Field

from .settings import CourseGeneratorSettings


class LectureTopic(BaseModel):
    """A topic covered by a [lecture][okcourse.models.Lecture] in a course."""
    number: int = Field(..., description="The position number of the lecture within the series.")
    title: str = Field(..., description="The topic of a lecture within a course.")
    subtopics: list[str] = Field(..., description="The subtopics covered in the lecture.")

    def __str__(self) -> str:
        subtopics_str = "\n".join(f"  - {sub}" for sub in self.subtopics) if self.subtopics else ""
        return f"Lecture {self.number}: {self.title}\n{subtopics_str}"


class CourseOutline(BaseModel):
    """The outline of a course, including its title and the topics covered by each [lecture][okcourse.models.Lecture]."""
    title: str = Field(..., description="The title of the course.")
    topics: list[LectureTopic] = Field(..., description="The topics covered by each lecture in the series.")

    def __str__(self) -> str:
        topics_str = "\n\n".join(str(topic) for topic in self.topics)
        return f"Course title: {self.title}\n\n{topics_str}"


class Lecture(LectureTopic):
    """A lecture in a [course][okcourse.models.Course], including its title text content."""
    text: str = Field(..., description="The unabridged text content of the lecture.")

    def __str__(self) -> str:
        return f"{self.title}\n\n{self.text}"


class Course(BaseModel):
    """A complete course, including its [outline][okcourse.models.CourseOutline] and [lectures][okcourse.models.Lecture]."""
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
    """The result of generating a course and its assets, including the [settings][okcourse.settings.CourseGeneratorSettings] used, the generated [course][okcourse.models.Course], and the paths to the generated course, audio, and image files."""
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
