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


class CoursePrompts(BaseModel):
    """Bundles the various prompts needed for a single type of course."""

    system: str = Field(
        None,
        description="The `system` prompt guides the language model's style and tone when generating the course outline "
        "and lecture text.",
    )
    outline: str = Field(
        None,
        description="The `outline` prompt contains the course outline generation instructions for the language model. "
        "On the AI model side, this is a 'user' prompt.",
    )
    lecture: str = Field(
        None,
        description="The lecture content generation instructions for the language model. On the AI model side, this is "
        "a 'user' prompt.",
    )
    image: str = Field(
        None,
        description="Guides the image model's generation of course cover art. On the AI model side, this is a 'user' "
        "prompt.",
    )


class CourseSettings(BaseModel):
    """Runtime-modifiable settings that configure the behavior of a course [`generator`][okcourse.generators].

    Create a `Course` instance and then modify its [`Course.settings`][okcourse.models.Course.settings] attribute, which
    is an instance of this class with default values. After configuring the course settings, pass the `Course` instance
    to a course generator's constructor and then to its
    [`generate_outline`][okcourse.generators.CourseGenerator.generate_outline] method to start generating course
    content.
    """

    prompts: CoursePrompts = Field(
        default_factory=CoursePrompts, description="The prompts that guide the AI models in course generation."
    )
    num_lectures: int = Field(4, description="The number of lectures that should generated for for the course.")
    num_subtopics: int = Field(4, description="The number of subtopics that should be generated for each lecture.")
    output_directory: Path = Field(
        Path("~/.okcourse").expanduser(),
        description="Directory for saving generated course content.",
    )
    text_model_outline: str = Field(
        "gpt-4o",
        description="The ID of the text generation model to use for generating course outlines.",
    )
    text_model_lecture: str = Field(
        "gpt-4o",
        description="The ID of the text generation model to use for generating course lectures.",
    )
    image_model: str = Field(
        "dall-e-3",
        description="The ID of the image generation model to use.",
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


class CourseGenerationInfo(BaseModel):
    """Details about the course generation, including okcourse version, tokent counts (input and output), and durations."""  # noqa: E501

    generator_type: str | None = Field(
        None,
        description="The type of course generator used to generate the course content.",
    )
    okcourse_version: str | None = Field(
        None,
        description="The version of the okcourse library used to generate the course.",
    )
    input_token_count: int = Field(
        0,
        description="The total number of tokens sent to the text completion endpoint when requesting content "
        "generation. This count includes the tokens sent in the outline and lecture prompts.",
    )
    output_token_count: int = Field(
        0,
        description="The total number of tokens returned by the text completion endpoint. Includes tokens return for "
        "all outline and lecture content generated.",
    )
    tts_character_count: int = Field(
        0,
        description="The total number of characters sent to the TTS endpoint.",
    )
    outline_gen_elapsed_seconds: float = Field(
        0.0,
        description="The time in seconds spent generating the course outline. This value is not cumulative and "
        "contains only the most recent outline generation time.",
    )
    lecture_gen_elapsed_seconds: float = Field(
        0.0,
        description="The time in seconds spent generating the course lectures. This value is not cumulative and "
        "contains only the most recent lecture generation time.",
    )
    image_gen_elapsed_seconds: float = Field(
        0.0,
        description="The time in seconds spent generating the course cover image. This value is not cumulative "
        "and contains only the most recent image generation time.",
    )
    audio_gen_elapsed_seconds: float = Field(
        0.0,
        description="The time in seconds spent generating and processing the course audio file. This value is not "
        "cumulative and contains only the most recent audio generation time. Processing includes combining the speech "
        "audio chunks into a single file and saving it to disk.",
    )
    num_images_generated: int = Field(
        0,
        description="The number of images generated for the course.",
    )
    audio_file_path: Path | None = Field(
        None, description="The path to the audio file generated from the course content."
    )
    image_file_path: Path | None = Field(None, description="The path to the cover image generated for the course.")


class Course(BaseModel):
    """A `Course` is the container for its content and the settings a course generator uses to generate that content.

    Create a `Course` instance, modify its [`settings`][okcourse.models.CourseSettings], and then pass the `Course` to a
    course generator like
    [`OpenAIAsyncGenerator`][okcourse.generators.OpenAIAsyncGenerator.generate_outline]. You can then start generating
    content with the generator's methods like [`generate_outline()`][okcourse.OpenAIAsyncGenerator.generate_outline].
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
    generation_info: CourseGenerationInfo = Field(
        default_factory=CourseGenerationInfo,
        description="Details about the course's content generation process, including the version of `okcourse` used, "
        "the token and character counts, and the time elapsed.",
    )

    def __str__(self) -> str:
        if not self.lectures:
            return str(self.outline)
        lectures_str = "\n\n".join(str(lecture) for lecture in self.lectures)
        return f"{self.outline}\n\n{lectures_str}"
