"""Abstract base class for generator subclasses that interact with AI service provider APIs to create course content.

Subclasses must implement the abstract methods on [`CourseGenerator`][okcourse.generators.base.CourseGenerator] and
add service provider-specific API interaction logic to generate the outline, lectures, image, and audio for a
course.

For example, the [`OpenAIAsyncGenerator`][okcourse.generators.openai.OpenAIAsyncGenerator] is an example of a subclass
that implements the `CourseGenerator`'s abstract methods to interact with OpenAI's API to generate course content.
"""

from abc import ABC, abstractmethod
from logging import getLogger as logger
from pathlib import Path
from ..models import Course
from ..prompt_library import ACADEMIC
from ..utils.log_utils import get_logger, get_top_level_version


class CourseGenerator(ABC):
    """Abstract base class for generating a course outline, its lectures, a cover image, and audio for the course.

    Args:
        course: The course to generate content for.

    Attributes:
        log: The logger for the generator.

    Subclasses must implement the abstract methods to generate the course outline, lectures, image, and audio.
    """

    def __init__(self, course: Course):
        # TODO: Assign in the subclass __init__ so the logs and CourseGenerationInfo have the subclass' name
        self.log: logger = None
        """The logger for the generator."""

        self._init_logger(course)
        self._init_generator_info(course)
        self._init_prompts(course)

    def _init_logger(self, course: Course) -> None:
        """Creates a logger whose name is derived from the CourseGenerator *subclass* at runtime."""

        if course.settings.log_level:
            # Use the actual subclass name and module at runtime
            source_name = f"{self.__module__}.{type(self).__name__}"
            log_file = course.settings.output_directory / Path(f"{source_name}.log")
            self.log = get_logger(
                source_name=source_name,
                level=course.settings.log_level,
                file_path=log_file if course.settings.log_to_file else None,
            )

            if course.settings.log_to_file:
                self.log.info(f"Logging to file: {log_file}")

    def _init_generator_info(self, course: Course) -> None:
        """Record the generator type and version in the Course object's generation_info."""

        course.generation_info.generator_type = f"{self.__module__}.{type(self).__name__}"
        course.generation_info.okcourse_version = get_top_level_version("okcourse")

    def _init_prompts(self, course: Course) -> None:
        if not course.settings.prompts:
            course.settings.prompts = ACADEMIC

    @abstractmethod
    def generate_outline(self, course: Course) -> Course:
        """Uses a generative pre-trained transformer (GPT) to generate an outline for the course based on its title.

        Modify the [`Course.settings`][okcourse.models.Course.settings] attribute before calling this method to
        customize the generation process and its output.

        Args:
            course: The course to generate an outline for.

        Returns:
            Course: The course with its [`outline`][okcourse.models.Course.outline] attribute set.
        """
        pass

    @abstractmethod
    def generate_lectures(self, course: Course) -> Course:
        """Uses a generative pre-trained transformer (GPT) to generate the lectures in the course outline.

        This method requires that the course has had its outline generated with a call to
        [`generate_outline`][okcourse.generators.base.CourseGenerator.generate_outline] before being passed to this
        method.

        Args:
            course: The course to generate lectures for. The given course must have had its outline generated and its
                [`outline`][okcourse.models.Course.outline] attribute set.

        Returns:
            Course: The course with its [`lectures`][okcourse.models.Course.lectures] attribute set.
        """
        pass

    @abstractmethod
    def generate_image(self, course: Course) -> Course:
        """Uses an image generation model to generate a cover image for the course based on its title.

        Args:
            course: The course to generate an image for.

        Returns:
            Course: The course with the [`image_file_path`][okcourse.models.CourseGenerationInfo.image_file_path]
                attribute set in its [`generation_info`][okcourse.models.Course.generation_info] attribute.
        """
        pass

    @abstractmethod
    def generate_audio(self, course: Course) -> Course:
        """Uses a text-to-speech (TTS) model to generate audio for the course from its lectures.

        This method requires that the course has had its lectures generated with a call to
        [`generate_lectures`][okcourse.generators.base.CourseGenerator.generate_lectures] before being passed to this
        method.

        Returns:
            Course: The course with the [`audio_file_path`][okcourse.models.CourseGenerationInfo.audio_file_path]
                attribute set in its [`generation_info`][okcourse.models.Course.generation_info] attribute.
        """
        pass
