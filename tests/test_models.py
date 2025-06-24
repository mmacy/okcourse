"""Unit tests for okcourse models."""

import pytest
from pathlib import Path
from logging import INFO

from okcourse.models import (
    CourseLectureTopic,
    CourseOutline,
    CourseLecture,
    CoursePromptSet,
    CourseSettings,
    CourseGenerationInfo,
    Course,
)


def test_course_lecture_topic_creation():
    """Test creating a CourseLectureTopic."""
    topic = CourseLectureTopic(
        number=1,
        title="Introduction to Python",
        subtopics=["Variables", "Data Types", "Control Flow"]
    )
    assert topic.number == 1
    assert topic.title == "Introduction to Python"
    assert len(topic.subtopics) == 3
    assert "Variables" in topic.subtopics


def test_course_lecture_topic_str():
    """Test string representation of CourseLectureTopic."""
    topic = CourseLectureTopic(
        number=2,
        title="Advanced Concepts",
        subtopics=["Classes", "Inheritance"]
    )
    str_repr = str(topic)
    assert "Lecture 2: Advanced Concepts" in str_repr
    assert "Classes" in str_repr
    assert "Inheritance" in str_repr


def test_course_outline_creation():
    """Test creating a CourseOutline."""
    topics = [
        CourseLectureTopic(number=1, title="Basics", subtopics=["Intro"]),
        CourseLectureTopic(number=2, title="Advanced", subtopics=["Expert"])
    ]
    outline = CourseOutline(title="Python Course", topics=topics)
    assert outline.title == "Python Course"
    assert len(outline.topics) == 2
    assert outline.topics[0].title == "Basics"


def test_course_lecture_creation():
    """Test creating a CourseLecture."""
    lecture = CourseLecture(
        number=1,
        title="Introduction",
        subtopics=["Overview"],
        text="This is the lecture content."
    )
    assert lecture.number == 1
    assert lecture.title == "Introduction"
    assert lecture.text == "This is the lecture content."
    assert "Overview" in lecture.subtopics


def test_course_prompt_set_creation():
    """Test creating a CoursePromptSet."""
    prompt_set = CoursePromptSet(
        description="Test prompts",
        system="You are a teacher.",
        outline="Create an outline.",
        lecture="Generate a lecture.",
        image="Create an image."
    )
    assert prompt_set.description == "Test prompts"
    assert prompt_set.system == "You are a teacher."
    assert prompt_set.outline == "Create an outline."


def test_course_settings_defaults():
    """Test default values in CourseSettings."""
    settings = CourseSettings()
    assert settings.num_lectures == 4
    assert settings.num_subtopics == 4
    assert settings.text_model_outline == "gpt-4o"
    assert settings.text_model_lecture == "gpt-4o"
    assert settings.image_model == "dall-e-3"
    assert settings.tts_model == "tts-1"
    assert settings.tts_voice == "alloy"
    assert settings.log_level == INFO
    assert settings.log_to_file is False


def test_course_settings_custom_values():
    """Test CourseSettings with custom values."""
    settings = CourseSettings(
        num_lectures=6,
        num_subtopics=3,
        text_model_outline="gpt-3.5-turbo",
        output_directory=Path("/tmp/test")
    )
    assert settings.num_lectures == 6
    assert settings.num_subtopics == 3
    assert settings.text_model_outline == "gpt-3.5-turbo"
    assert settings.output_directory == Path("/tmp/test")


def test_course_generation_info_defaults():
    """Test default values in CourseGenerationInfo."""
    info = CourseGenerationInfo()
    assert info.okcourse_version is None
    assert info.generator_type is None
    assert info.lecture_input_token_count == 0
    assert info.lecture_output_token_count == 0
    assert info.outline_input_token_count == 0
    assert info.outline_output_token_count == 0
    assert info.tts_character_count == 0
    assert info.outline_gen_elapsed_seconds == 0.0
    assert info.lecture_gen_elapsed_seconds == 0.0
    assert info.image_gen_elapsed_seconds == 0.0
    assert info.audio_gen_elapsed_seconds == 0.0
    assert info.num_images_generated == 0
    assert info.audio_file_path is None
    assert info.image_file_path is None


def test_course_creation():
    """Test creating a Course."""
    course = Course(title="Test Course")
    assert course.title == "Test Course"
    assert course.outline is None
    assert course.lectures is None
    assert isinstance(course.settings, CourseSettings)
    assert isinstance(course.generation_info, CourseGenerationInfo)


def test_course_with_outline():
    """Test Course with an outline."""
    topics = [CourseLectureTopic(number=1, title="Topic 1", subtopics=["Sub1"])]
    outline = CourseOutline(title="Course Title", topics=topics)
    course = Course(title="Test", outline=outline)
    assert course.outline is not None
    assert course.outline.title == "Course Title"
    assert len(course.outline.topics) == 1


def test_course_with_lectures():
    """Test Course with lectures."""
    lectures = [
        CourseLecture(number=1, title="Lecture 1", subtopics=["Sub1"], text="Content 1"),
        CourseLecture(number=2, title="Lecture 2", subtopics=["Sub2"], text="Content 2")
    ]
    course = Course(title="Test", lectures=lectures)
    assert course.lectures is not None
    assert len(course.lectures) == 2
    assert course.lectures[0].title == "Lecture 1"
    assert course.lectures[1].text == "Content 2"


def test_course_str_without_lectures():
    """Test Course string representation without lectures."""
    topics = [CourseLectureTopic(number=1, title="Topic 1", subtopics=["Sub1"])]
    outline = CourseOutline(title="Course Title", topics=topics)
    course = Course(title="Test", outline=outline)
    str_repr = str(course)
    assert "Course title: Course Title" in str_repr
    assert "Topic 1" in str_repr


def test_course_str_with_lectures():
    """Test Course string representation with lectures."""
    topics = [CourseLectureTopic(number=1, title="Topic 1", subtopics=["Sub1"])]
    outline = CourseOutline(title="Course Title", topics=topics)
    lectures = [CourseLecture(number=1, title="Lecture 1", subtopics=["Sub1"], text="Content")]
    course = Course(title="Test", outline=outline, lectures=lectures)
    str_repr = str(course)
    assert "Course title: Course Title" in str_repr
    assert "Lecture 1" in str_repr
    assert "Content" in str_repr