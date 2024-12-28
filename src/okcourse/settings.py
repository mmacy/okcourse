"""Settings used during the course generation process and a set of default values.

Attributes:
    default_settings (CourseGeneratorSettings): A set of runtime-modifiable defaults for course generation. You're
        expected to modify at least the `course_title` prior to course generation.
"""

from logging import INFO
from pathlib import Path

from pydantic import BaseModel, Field


class CourseGeneratorSettings(BaseModel):
    """To configure course generation, pass an instance of this class to a [CourseGenerator][okcourse.generators.CourseGenerator] constructor.  # noqa: E501

    `CourseGeneratorSettings` contains runtime-modifiable settings used by the library to guide AI models in generating
    course content. You should modify at least the `course_title` before generating a course.

    Attributes:
        course_title (str | None): The title of the course, or `None` if not set.
        num_lectures (int): The number of lectures to generate for the course.
            This setting heavily influences API usage and thus the cost of course
            generation (more lectures means higher cost).
        output_directory (Path): The directory where generated files and logs
            will be saved.
        generate_image (bool): Whether to generate cover images for the course.
        generate_audio (bool): Whether to generate audio files for the course.
        text_model (str): The ID of the text generation model to use.
        text_model_system_prompt (str): The `system` prompt to send to the text
            model when generating the course content.
        text_model_outline_prompt (str | None): The `user` prompt to send to the
            text model for generating the course outline, or `None` if not set.
        text_model_lecture_prompt (str | None): The `user` prompt to send to the
            text model for generating lecture content, or `None` if not set.
        image_model (str): The ID of the image generation model to use.
        image_model_prompt (str): The `user` prompt to send to the image model
            for generating course cover art.
        tts_model (str): The ID of the text-to-speech model to use.
        tts_voice (str): The voice to use for text-to-speech audio generation.
        max_concurrent_requests (int): The maximum number of concurrent
            asynchronous requests during generation.
        log_level (int | None): Log level for course generation operations. Specify a
            [Python logging level](https://docs.python.org/3/library/logging.html#logging-levels)
            like `INFO`, `DEBUG`, `WARNING`, `ERROR`, or `CRITICAL`.
            To disable logging, specify `None`."
        log_to_file (bool): Whether to log to a file in the output directory.
    """

    course_title: str = Field(
        "Artificial Super Intelligence: Paperclips All The Way Down",
        description="The title of the course guides generation of the course outline and the content of its lectures.",
    )
    num_lectures: int = Field(2, description="The number of lectures that should generated for for the course.")
    output_directory: Path = Field(
        Path("~/.okcourse").expanduser(),  # TODO: Make this cross-platform-friendly
        description="Directory for saving generated course content.",
    )
    generate_image: bool = Field(
        False,
        description="Whether to generate a cover image for the course. If `True`, this image is used as the album art "
        "tag for the audio file and also saved to disk in the [`output_directory`][output_directory].",
    )
    generate_audio: bool = Field(
        False,
        description="Whether to generate an audio file containing the course lectures. "
        "If `True`, the audio file is saved to disk in the [`output_directory`][output_directory].",
    )
    text_model: str = Field(
        "gpt-4o",
        description="The ID of the text generation model to use.",
    )
    text_model_system_prompt: str = Field(
        "You are an esteemed college professor and expert in your field who typically lectures graduate students. "
        "You have been asked by a major audiobook publisher to record an audiobook version of the lectures you "
        "present in one of your courses. You have been informed by the publisher that the listeners of the audiobook are "  # noqa: E501
        "knowledgeable in the subject area and will listen to your course to gain intermediate- to expert-level knowledge. "  # noqa: E501
        "Your lecture style is professional, direct, and deeply technical.",
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
        "Generate the complete unabridged text for a lecture titled '${lecture_title}' in a graduate-level course named "  # noqa: E501
        "'${course_title}'. The lecture should be written in a style that lends itself well to being recorded "
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
        "Create an image in the style of cover art for an audio recording of a college lecture series shown in an online "  # noqa: E501
        "academic catalog. The image should clearly convey the subject of the course to customers browsing the courses on "  # noqa: E501
        "the vendor's site. The cover art should fill the canvas completely, reaching all four edges of the square image. "  # noqa: E501
        "Its style should reflect the academic nature of the course material and be indicative of the course content. "
        "The title of the course is '${course_title}'",
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


default_generator_settings = CourseGeneratorSettings()
"""Starting point for course generation settings. Modify at least `course_title` before generating a course."""
