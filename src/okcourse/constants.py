"""Global defaults."""

TEXT_MODEL = "gpt-4o"
SPEECH_MODEL = "tts-1"
TTS_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
IMAGE_MODEL = "dall-e-3"
MAX_LECTURES = 100
MAX_CONCURRENT_TASKS = 32

AI_DISCLAIMER = (
    "This is an AI-generated voice, not a human, presenting AI-generated content that might be biased or inaccurate."
)
"""Disclaimer required by OpenAI's usage policy."""

SYSTEM_PROMPT = (
    "You are an esteemed college professor and expert in your field who typically lectures graduate students. "
    "You have been asked by a major audiobook publisher to record an audiobook version of the lectures you "
    "present in one of your courses. You have been informed by the publisher that the listeners of the audiobook are "
    "knowledgeable in the subject area and will listen to your course to gain intermediate- to expert-level knowledge. "
    "Your lecture style is professional, direct, and deeply technical."
)
"""System prompt for the lecture outline and lecture text generation requests sent to OpenAI."""

IMAGE_PROMPT = (
    "Create an image in the style of cover art for an audio recording of a college lecture series shown in an online "
    "academic catalog. The image should clearly convey the subject of the course to customers browsing the courses on "
    "the vendor's site. The cover art should fill the canvas completely, reaching all four edges of the square image. "
    "Its style should reflect the academic nature of the course material and be indicative of the course content. "
    "The title of the course is:\n\n"
)
"""Prompt passed to OpenAI's `/image` endpoint. The course title is appended to this prompt before sending the
image generation request."""

LLM_SMELLS = {
    "crucial": "important",
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
"""Words that tend to be overused by OpenAI's text generation models and their simplified forms.

By default, overused keys are replaced by their simplified values in lecture text to help reduce \"LLM smell.\""""
