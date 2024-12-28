from abc import ABC, abstractmethod
from logging import getLogger as logger
from pathlib import Path
from ..settings import CourseGeneratorSettings, default_generator_settings
from ..models import CourseGenerationResult
from ..utils import get_logger


class CourseGenerator(ABC):
    """
    Abstract base class for generating a course outline, its lectures, a cover image, and audio for the course.

    Attributes:
        settings: The settings used for course generation.

    Subclasses must implement the abstract methods to generate the course outline, lectures, image, and audio.
    """

    def __init__(self, generation_settings: CourseGeneratorSettings = default_generator_settings):
        self.settings: CourseGeneratorSettings = generation_settings
        self.result: CourseGenerationResult = CourseGenerationResult(settings=self.settings)
        self.log: logger = None

        if self.settings.log_level:
            self.log = get_logger(
                source_name=__name__,
                level=self.settings.log_level,
                file_path=self.settings.output_directory / Path(__name__).with_suffix(".log")
                if self.settings.log_to_file
                else None,
            )

    @abstractmethod
    def generate_outline(self, course_title: str | None = None) -> CourseGenerationResult:
        """Generates an outline for a course with the specified title.

        Args:
            course_title: The title of the course. If not provided, the title from the settings is used.

        Returns:
            CourseGenerationResult: The result of the generation process with its `course.outline` attribute set.
        """
        pass

    @abstractmethod
    def generate_lectures(self) -> CourseGenerationResult:
        """Generates lectures for the course and saves the course and its outline to the path specified in the settings.

        Returns:
            CourseGenerationResult: The result of the generation process with its `course.lectures` and `course_file`
            attributes set.
        """
        pass

    @abstractmethod
    def generate_image(self) -> CourseGenerationResult:
        """Generates a cover image for the course and saves it to the path specified in the settings.

        Returns:
            CourseGenerationResult: The result of the generation process with its `image_file` attribute set.
        """
        pass

    @abstractmethod
    def generate_audio(self) -> CourseGenerationResult:
        """Generates audio for the course and saves it to the path specified in the settings.

        Args:
            output_path: The path where the audio file will be saved.
        """
        pass
