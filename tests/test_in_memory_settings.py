from okcourse.models import CourseSettings, CourseGenerationInfo


def test_in_memory_settings_default():
    settings = CourseSettings()
    assert settings.in_memory_output is False


def test_in_memory_settings_true():
    settings = CourseSettings(in_memory_output=True)
    assert settings.in_memory_output is True


def test_generation_info_memory_fields():
    info = CourseGenerationInfo()
    assert info.image_bytes is None
    assert info.audio_bytes is None

