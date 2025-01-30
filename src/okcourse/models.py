"""[Pydantic](https://docs.pydantic.dev/) models representing a course and its generation settings, outline, and lectures."""  # noqa: E501

from logging import INFO
from pathlib import Path

from pydantic import BaseModel, Field


class CourseLectureTopic(BaseModel):
    """A topic covered by a [lecture][okcourse.models.CourseLecture] in a course."""

    number: int = Field(..., description="The position number of the lecture within the series.")
    title: str = Field(..., description="The topic of a lecture within a course.")
    subtopics: list[str] = Field(..., description="The subtopics covered in the lecture.")

    def __str__(self) -> str:
        subtopics_str = "\n".join(f"  - {sub}" for sub in self.subtopics) if self.subtopics else ""
        return f"Lecture {self.number}: {self.title}\n{subtopics_str}"


class CourseOutline(BaseModel):
    """The outline of a course, including its title and the topics covered by each [lecture][okcourse.models.CourseLecture]."""  # noqa: E501

    title: str = Field(..., description="The title of the course.")
    topics: list[CourseLectureTopic] = Field(..., description="The topics covered by each lecture in the series.")

    def __str__(self) -> str:
        topics_str = "\n\n".join(str(topic) for topic in self.topics)
        return f"Course title: {self.title}\n\n{topics_str}"


class CourseLecture(CourseLectureTopic):
    """A lecture in a [course][okcourse.models.Course], including its title text content."""

    text: str = Field(..., description="The unabridged text content of the lecture.")

    def __str__(self) -> str:
        return f"{self.title}\n\n{self.text}"


class CoursePromptSet(BaseModel):
    """Bundles a set of prompts used for generating a certain type of course, like academic, storytelling, or technical."""  # noqa: E501

    description: str = Field(
        "`system` and `user` prompts appropriate for a certain type of course.",
        description="A name or description for the type of course this collection of prompts is intended to create.",
    )
    system: str = Field(
        None,
        description="The `system` prompt guides the language model's style and tone when generating the course outline "
        "and lecture text. This prompt should be appropriate for passing to the AI service provider's API along with "
        "any of the other prompts (the outline, lecture, or image prompts)",
    )
    outline: str = Field(
        None,
        description="The `user` prompt that contains the course outline generation instructions for the language "
        "model. This prompt is passed along with the `system` prompt when requesting an outline.",
    )
    lecture: str = Field(
        None,
        description="The `user` prompt that contains the lecture content generation instructions for the language "
        "model. This prompt is passed along with the `system` prompt when requesting one of the lectures in the course.",
    )
    image: str = Field(
        None,
        description="The `user` prompt that guides the image model's generation of course cover art. This prompt is "
        "passed along with the `system` prompt when requesting a cover image for the course.",
    )


_DEFAULT_PROMPT_SET = CoursePromptSet(
    description="Academic lecture series",

    system="You are an esteemed college professor and expert in your field who typically lectures graduate students. "
    "You have been asked by a major book publisher to record an audio version of the lectures in one of your courses. "
    "The listeners of the audio version of your course have intermediate-level knowledgeable in the subject matter and "
    "and will listen to your course to gain expert-level knowledge. Your lecture style is professional, direct, and "
    "deeply technical.",

    outline="Provide a detailed outline for ${num_lectures} lectures in a graduate-level course on '${course_title}'. "
    "List each lecture title numbered. Each lecture should have ${num_subtopics} subtopics listed after the "
    "lecture title. Respond only with the outline, omitting any other commentary.",

    lecture="Generate the complete unabridged text for a lecture titled '${lecture_title}' in a graduate-level course "
    "named '${course_title}'. The lecture should be written in a style that lends itself well to being read aloud and "
    "recorded but should not divulge this guidance. There will be no audience present for the recording of the lecture "
    "and no audience should be addressed or referenced the lecture text. Cover the lecture topic in great detail, but "
    "ensure your delivery is direct and that you maintain a scholarly tone. "
    "Aim for a final product whose textual content flows smoothly when read aloud and can be easily understood without "
    "visual aids. Produce clean text that lacks markup, lists, code, mathematical formulae, or other formatting that "
    "can interfere with text-to-speech processing. Ensure the content is original and does not duplicate content "
    "from the other lectures in the series:\n\n${course_outline}",

    image="Create a cover image for a book titled '${course_title}'. The style should mirror that of realistic, "
    "detail-oriented, and formal art common in the early 19th-century. The use of muted colors and textures resembling "
    "a chalkboard is desired. Add educational symbols, including books, scrolls, and quills to emphasize the academic "
    "aspect. The series title should be hand-drawn in an old academic script with a chalk-like effect.",
)
"""The default "academic" set of prompts used by a course generator like the [`OpenAIAsyncGenerator`][okcourse.OpenAIAsyncGenerator].

You should not reference this prompt set directly - use the [`ACADEMIC`][okcourse.prompt_library.ACADEMIC] prompt set in
the `prompt_library` module instead (it's an alias of this one).
"""


class CourseSettings(BaseModel):
    """Runtime-modifiable settings that configure the behavior of a course [`generator`][okcourse.generators].

    Create a `Course` instance and then modify its [`Course.settings`][okcourse.models.Course.settings] attribute, which
    is an instance of this class with default values. After configuring the course settings, pass the `Course` instance
    to a course generator's constructor and then to its
    [`generate_outline`][okcourse.generators.CourseGenerator.generate_outline] method to start generating course
    content.
    """

    prompts: CoursePromptSet = Field(
        _DEFAULT_PROMPT_SET,
        description="The prompts that guide the AI models in course generation.",
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
    """Details about the course generation, including okcourse version, token counts (input and output), and durations.

    You can estimate the cost of course generation based on the token count values in this class and the models that
    were used to produce them. The model names are specified in the [`CourseSettings`][okcourse.CourseSettings] and most
    AI service providers make cost-per-token pricing available on their website, which may vary by provider and your
    account or subscription level.
    """

    okcourse_version: str | None = Field(
        None,
        description="The version of the okcourse library used to generate the course.",
    )
    generator_type: str | None = Field(
        None,
        description="The type of course generator used to generate the course content.",
    )
    lecture_input_token_count: int = Field(
        0,
        description="The total number of tokens sent to the text completion endpoint when requesting the lecture "
        "content for the course. This count does NOT include the tokens sent when requesting the outline.",
    )
    lecture_output_token_count: int = Field(
        0,
        description="The total number of tokens returned by the text completion endpoint is response to lecture "
        "generation request for the course. This count does NOT include the tokens returned for outline requests.",
    )
    outline_input_token_count: int = Field(
        0,
        description="The total number of tokens sent to the text completion endpoint when requesting the outline(s) "
        "for the course. This count does NOT include the tokens sent when requesting the course's lecture content.",
    )
    outline_output_token_count: int = Field(
        0,
        description="The total number of tokens returned by the text completion endpoint is response to outline "
        "generation requests for the course. This count does NOT include the tokens returned for lecture requests.",
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
        description="The topic of the course and its lectures. The course title, along with its "
        "[`settings.prompts`][okcourse.models.CourseSettings.prompts], are the most "
        "influential in determining the course content.",
    )
    outline: CourseOutline | None = Field(
        None, description="The outline for the course that defines the topics for each lecture."
    )
    lectures: list[CourseLecture] | None = Field(None, description="The lectures that comprise the complete course.")
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
