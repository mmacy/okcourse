"""Pydantic model classes representing a course and its components like the outline, lecture topics, and lectures."""

from pathlib import Path
from string import Template

from pydantic import BaseModel, Field


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
    lectures: list[Lecture] = Field(..., description="The lectures that comprise the complete course.")

    def __str__(self) -> str:
        lectures_str = "\n\n".join(str(lecture) for lecture in self.lectures)
        return f"{self.outline}\n\n{lectures_str}"

    @property
    def title(self) -> str:
        return self.outline.title


class CourseGeneratorSettings(BaseModel):
    course_title: str | None = Field(None, description="The title of the course, or `None` if it hasn't been set.")
    num_lectures: int = Field(..., description="The number of lectures to generate for the course.")
    output_directory: Path = Field(Path.cwd(), description="The directory where the course files and the generation log will be saved. If logging is enabled by setting a ``log_level``, the log file is also written to this directory."),
    generate_image: bool = Field(..., description="Whether to generate cover images for the course audio files.")
    generate_audio: bool = Field(..., description="Whether to generate audio files for the course lectures.")
    log_level: int | None = Field(..., description="The log message level to use during the course generation process, or `None` to disable logging.")
    text_model: str = Field(..., description="The ID of the text generation model to use for generating the lecture content.")
    text_model_system_prompt: str = Field(..., description="The `system` prompt to send to the text model when generating the course outline and lecture content.")
    text_model_outline_prompt: str = Field(..., description="The `user` prompt to send to the text model for generating the course outline.")
    text_model_lecture_prompt: str = Field(..., description="The `user` prompt to send to the text model for generating the lecture content.")
    image_model: str = Field(..., description="The ID of the image generation model to use for generating course cover art.")
    image_model_prompt: str = Field(..., description="The `user` prompt to send to the image model for image generation.")
    tts_model: str = Field(..., description="The ID of the text-to-speech model to use for audio generation.")
    tts_voice: str = Field(..., description="The text-to-speech voice to use for audio generation.")
    max_concurrent_requests: int = Field(..., description="For async generators, sets maximum number of concurrent asynchronous requests to make during the course generation process. This setting is ignored by synchronous generators.")


class CourseGenerationResult(BaseModel):
    course: Course | None = Field(..., description="The generated course model or `None` if the course has yet to be generated.")
    settings: CourseGeneratorSettings = Field(..., description="The settings used to generate the course.")
    course_file: Path = Field(..., description="The path to the JSON file containing the course outline and lecture content. The JSON file contains the output of `course.model_dump_json()`).")
    audio_file: Path | None = Field(None, description="The path to the generated audio file if audio generation was enabled.")
    image_file: Path | None = Field(None, description="The path to the generated cover image file if image generation was enabled.")
