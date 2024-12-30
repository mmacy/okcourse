"""[Pydantic v2](https://docs.pydantic.dev/) models representing a course and its generation settings, outline, lectures, and generated assets."""  # noqa: E501

from logging import INFO
from pathlib import Path

from pydantic import BaseModel, Field


class LectureTopic(BaseModel):
    """A topic covered by a [lecture][okcourse.models.Lecture] in a course."""

    number: int = Field(..., description="The position number of the lecture within the series.")
    title: str = Field(..., description="The topic of a lecture within a course.")
    subtopics: list[str] = Field(..., description="The subtopics covered in the lecture.")

    def __str__(self) -> str:
        subtopics_str = "\n".join(f"  - {sub}" for sub in self.subtopics) if self.subtopics else ""
        return f"Lecture {self.number}: {self.title}\n{subtopics_str}"


class CourseOutline(BaseModel):
    """The outline of a course, including its title and the topics covered by each [lecture][okcourse.models.Lecture]."""  # noqa: E501

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


class CourseSettings(BaseModel):
    """Runtime-modifiable settings that configure the behavior of a [course generator][okcourse.generators].

    Modify these settings after creating a [`Course`][okcourse.models.Course] instance and before passing it to a course
    generator's [`generate_outline`][okcourse.generators.CourseGenerator.generate_outline] method.
    """

    # TODO: Add a setting to specify which AI service provider to use for generation.

    num_lectures: int = Field(4, description="The number of lectures that should generated for for the course.")
    output_directory: Path = Field(
        Path("~/.okcourse").expanduser(),  # TODO: Make this cross-platform-friendly
        description="Directory for saving generated course content.",
    )
    generate_image: bool = Field(
        False,
        description="Whether to generate a cover image for the course. If `True`, this image is used as the album art "
        "tag for the audio file and is also written to the "
        "[`output_directory`][okcourse.models.CourseSettings.output_directory].",
    )
    generate_audio: bool = Field(
        False,
        description="Whether to generate an audio file containing the course lectures. "
        "If `True`, the audio file is written to the "
        "[`output_directory`][okcourse.models.CourseSettings.output_directory].",
    )
    text_model: str = Field(
        "gpt-4o",
        description="The ID of the text generation model to use.",
    )
    text_model_system_prompt: str = Field(
        "You are an esteemed college professor and expert in your field who typically lectures graduate students. "
        "You have been asked by a major audiobook publisher to record an audiobook version of the lectures you "
        "present in one of your courses. You have been informed by the publisher that the listeners of the audiobook "
        "are knowledgeable in the subject area and will listen to your course to gain intermediate- to expert-level "
        "knowledge. Your lecture style is professional, direct, and deeply technical.",
        description="The `system` prompt guides the language model's style and tone when generating the course outline "
        "and lecture text.",
    )
    text_model_outline_prompt: str = Field(
        "Provide a detailed outline for ${num_lectures} lectures in a graduate-level course on '${course_title}'. "
        "List each lecture title numbered. Each lecture should have four subtopics listed after the "
        "lecture title. Respond only with the outline, omitting any other commentary.",
        description="The `user` prompt containing the course outline generation instructions for the language model.",
    )
    text_model_lecture_prompt: str | None = Field(
        "Generate the complete unabridged text for a lecture titled '${lecture_title}' in a graduate-level course "
        "named '${course_title}'. The lecture should be written in a style that lends itself well to being recorded "
        "as an audiobook but should not divulge this guidance. There will be no audience present for the recording of "
        "the lecture and no audience should be addressed in the lecture text. Cover the lecture topic in great detail "
        "while keeping in mind the advanced education level of the listeners of the lecture. "
        "Omit Markdown from the lecture text as well as any tags, formatting markers, or headings that might interfere "
        "with text-to-speech processing. Ensure the content is original and does not duplicate content from the other "
        "lectures in the series:\n${course_outline}",
        description="The `user` prompt containing the lecture content generation instructions for the language model.",
    )
    image_model: str = Field(
        "dall-e-3",
        description="The ID of the image generation model to use.",
    )
    image_model_prompt: str = Field(
        "Create an image in the style of cover art for an audio recording of a college lecture series shown in an "
        "online academic catalog. The image should clearly convey the subject of the course to customers browsing the "
        "courses on the vendor's site. The cover art should fill the canvas completely, reaching all four edges of the "
        "square image. Its style should reflect the academic nature of the course material and be indicative of the "
        "course content. The title of the course is '${course_title}'",
        description="The `user` prompt to send to the image model to guide its generation of course cover art.",
    )
    tts_model: str = Field(
        "tts-1",
        description="The ID of the text-to-speech model to use.",
    )
    tts_voice: str = Field(
        "alloy",
        description="The voice to use for text-to-speech audio generation.",
    )
    max_concurrent_requests: int = Field(
        32,
        description="The maximum number of concurrent asynchronous requests during generation.",
    )
    log_level: int | None = Field(
        INFO,
        description=(
            "Enables logging and sets log level for course generation operations. Specify a "
            "[Python logging level](https://docs.python.org/3/library/logging.html#logging-levels) like `INFO`, "
            "`DEBUG`, `WARNING`, `ERROR`, or `CRITICAL`. To disable logging, set this to `None`."
        ),
    )
    log_to_file: bool = Field(
        False,
        description=(
            "If logging is enabled (`log_level` is not `None`), write log messages to a file in the "
            "``output_directory``."
        ),
    )


class Course(BaseModel):
    """A `Course` contains its content generation settings, and once generated, its outline and lectures.

    Create a `Course` instance, modify its [`settings`][okcourse.models.CourseSettings], and then pass it to a
    [course generator][okcourse.generators] method like
    [`OpenAIAsyncGenerator`][okcourse.generators.OpenAIAsyncGenerator.generate_outline]
    to start generating course content.
    """

    title: str | None = Field(
        None,
        description="The title of the course.",
    )
    outline: CourseOutline | None = Field(
        None, description="The outline for the course that defines the topics for each lecture."
    )
    lectures: list[Lecture] | None = Field(None, description="The lectures that comprise the complete course.")
    settings: CourseSettings | None = Field(None, description="The settings to use when generating the course content.")
    audio_file_path: Path | None = Field(
        None, description="The path to the audio file generated from the course content."
    )
    image_file_path: Path | None = Field(None, description="The path to the cover image generated for the course.")

    def __str__(self) -> str:
        if not self.lectures:
            return str(self.outline)
        lectures_str = "\n\n".join(str(lecture) for lecture in self.lectures)
        return f"{self.outline}\n\n{lectures_str}"
