"""[Pydantic](https://docs.pydantic.dev/) models representing a course and its generation settings, outline, and lectures."""  # noqa: E501

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
    """Runtime-modifiable settings that configure the behavior of a course [`generator`][okcourse.generators].

    Create a `Course` instance and then modify its [`Course.settings`][okcourse.models.Course.settings] attribute, which
    is an instance of this class with default values. After configuring the course settings, pass the `Course` instance
    to a course generator's constructor and then to its
    [`generate_outline`][okcourse.generators.CourseGenerator.generate_outline] method to start generating course
    content.
    """

    # TODO: Add a setting to specify which AI service provider to use for generation.

    num_lectures: int = Field(4, description="The number of lectures that should generated for for the course.")
    output_directory: Path = Field(
        Path("~/.okcourse").expanduser(),  # TODO: Make this cross-platform-friendly
        description="Directory for saving generated course content.",
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
    log_level: int | None = Field(
        INFO,
        description=(
            "Specifies the [Python logging level](https://docs.python.org/3/library/logging.html#logging-levels) for "
            "course and course asset generation operations. Set this attribute to one of the Python standard library's"
            "[logging levels](https://docs.python.org/3/library/logging.html#logging-levels): `INFO`, `DEBUG`, "
            "`WARNING`, `ERROR`, or `CRITICAL`. To disable logging, set this attribute to `None`."
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
    """A `Course` is the container for its content and the settings a course generator uses to generate that content.

    Create a `Course` instance, modify its [`settings`][okcourse.models.CourseSettings], and then pass it to a
    course [`generator`][okcourse.generators] method like
    [`OpenAIAsyncGenerator`][okcourse.generators.OpenAIAsyncGenerator.generate_outline]
    to start generating course content.
    """

    title: str | None = Field(
        None,
        description="The topic of the course and its lectures. The course title, along with the "
        "[`text_model_outline_prompt`][okcourse.models.CourseSettings.text_model_outline_prompt], are the most "
        "influential in determining the course content.",
    )
    outline: CourseOutline | None = Field(
        None, description="The outline for the course that defines the topics for each lecture."
    )
    lectures: list[Lecture] | None = Field(None, description="The lectures that comprise the complete course.")
    settings: CourseSettings = Field(
        default_factory=CourseSettings,
        description="Course [`generators`][okcourse.generators] use these settings to determine the content of the "
        "course as well as the behavior of the generation process. Modify these settings to specify the number of "
        "lectures to generate for the course, the AI models to use to generate them, the output directory for the "
        "generated content, and more.",
    )
    audio_file_path: Path | None = Field(
        None, description="The path to the audio file generated from the course content."
    )
    image_file_path: Path | None = Field(None, description="The path to the cover image generated for the course.")

    def __str__(self) -> str:
        if not self.lectures:
            return str(self.outline)
        lectures_str = "\n\n".join(str(lecture) for lecture in self.lectures)
        return f"{self.outline}\n\n{lectures_str}"
