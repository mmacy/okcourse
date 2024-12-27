"""Globally accessible configuration and library defaults."""

__all__ = [
    "AI_DISCLAIMER",
    "DEFAULT_IMAGE_MODEL",
    "DEFAULT_IMAGE_PROMPT",
    "DEFAULT_SYSTEM_PROMPT",
    "DEFAULT_TEXT_MODEL",
    "DEFAULT_TTS_MODEL",
    "LLM_SMELLS",
    "MAX_LECTURES",
    "TTS_VOICES",
]

DEFAULT_TEXT_MODEL = "gpt-4o"
"""Name of the AI model to use for generating the course outline and lecture text."""

DEFAULT_TTS_MODEL = "tts-1"
"""Name of the AI model to use for generating the course audio file."""

TTS_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
"""List of voices available for the text-to-speech model. Determines the voice of the lecturer in the course audio file.

Voice samples are available on
[platform.openai.com/.../text-to-speech](https://platform.openai.com/docs/guides/text-to-speech).
"""

DEFAULT_IMAGE_MODEL = "dall-e-3"
"""Name of the AI model to use for generating the cover image for the course audio file."""

MAX_LECTURES = 100
"""Maximum number of lectures that may be generated for a course.

This limit is imposed to help avoid accidental excessive API usage and its associated cost rather than being a technical
limitation.
"""

AI_DISCLAIMER = (
    "This is an AI-generated voice, not a human, presenting AI-generated content that might be biased or inaccurate."
)
"""Disclaimer required by the [OpenAI usage policy](https://openai.com/policies/usage-policies/).

This disclaimer is inserted as the first line in the course audio.
"""

DEFAULT_SYSTEM_PROMPT = (
    "You are an esteemed college professor and expert in your field who typically lectures graduate students. "
    "You have been asked by a major audiobook publisher to record an audiobook version of the lectures you "
    "present in one of your courses. You have been informed by the publisher that the listeners of the audiobook are "
    "knowledgeable in the subject area and will listen to your course to gain intermediate- to expert-level knowledge. "
    "Your lecture style is professional, direct, and deeply technical."
)
"""System prompt for the lecture outline and lecture text generation requests sent to OpenAI."""

DEFAULT_IMAGE_PROMPT = (
    "Create an image in the style of cover art for an audio recording of a college lecture series shown in an online "
    "academic catalog. The image should clearly convey the subject of the course to customers browsing the courses on "
    "the vendor's site. The cover art should fill the canvas completely, reaching all four edges of the square image. "
    "Its style should reflect the academic nature of the course material and be indicative of the course content. "
    "The title of the course is:\n\n"
)
"""The prompt sent to the [`IMAGE_MODEL`][okcourse.constants.IMAGE_MODEL] when requesting a cover image for the course.

The user-specified course title is appended to this prompt before sending the request to the OpenAI API with
[`Completions.create()`][src.openai.resources.Completions.create].
"""

LLM_SMELLS = {  # TODO: Add support for phrases like "such as" (like) and "in order to" (to).
    # "crucial": "important",  # TODO: Uncomment when we can handle phrases (breaks right now due to a/an mismatch).
    "delve": "dig",
    "delved": "dug",
    "delves": "digs",
    "delving": "digging",
    "utilize": "use",
    "utilized": "used",
    "utilizing": "using",
    "utilization": "usage",
    "meticulous": "careful",
    "meticulously": "carefully",
}
"""Dictionary with key/value pairs of words overused by OpenAI's language models and their simplified forms.

Words in the keys are replaced by their simplified forms in generated lecture text to help reduce \"LLM smell.\"
"""
