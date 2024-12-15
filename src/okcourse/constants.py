TEXT_MODEL = "gpt-4o"
SPEECH_MODEL = "tts-1"
SPEECH_VOICE = "nova"
IMAGE_MODEL = "dall-e-3"

AI_DISCLAIMER = (
    "This is an AI-generated voice, not a human, presenting AI-generated content that might be biased or inaccurate."
)
"""Disclaimer required by OpenAI's usage policy."""

SYSTEM_PROMPT = (
    "You are an esteemed college professor and expert in your field who regularly lectures graduate "
    "students. You have been asked by a major audiobook publisher to record an audiobook version of a lecture series. "
    "Your lecture style is professional, direct, and highly technical."
)
"""System prompt for the lecture outline and lecture text generation requests sent to OpenAI."""

IMAGE_PROMPT = (
    "Create an image in the style typical of digitial cover art for downloadable podcasts in MP3 format. The cover "
    "image should clearly indicate the content of the podcast to customers browsing the podcast vendor's site. "
    "The image should be appropriate to accompany the digital distribution of an audio-only recording of the "
    "following college lecture series:\n\n"
)
"""Prompt passed to OpenAI's `/image` endpoint. The lecture series title is appended to this prompt before sending the
image generation request."""

LLM_SMELLS = {
    "crucial": "important",
    "delve": "dig",
    "delved": "dug",
    "delves": "digs",
    "delving": "digging",
    "utilize": "use",
    "utilized": "used",
    "utilizing": "using"
}
"""Words that tend to be overused by OpenAI's text generation models and their simplified forms.

By default, the overused words are replaced by their simplified forms in lecture text to help reduce \"LLM smell.\""""
