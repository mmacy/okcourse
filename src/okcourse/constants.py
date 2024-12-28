"""Immutable constant values.

These values define constraints not intended to be modified by `okcourse` library users. In some cases, they're driven
by policy or practical considerations rather than technical limitations.

For example, `MAX_LECTURES` is intended to prevent accidental excessive API usage and the potentially excessive cost
incurred by it.

Attributes:
    AI_DISCLAIMER (str): Disclaimer required by the OpenAI usage policy and likely other AI service providers.
    MAX_LECTURES (int): Maximum number of lectures that may be generated for a course.
"""

MAX_LECTURES = 100
"""Maximum number of lectures that may be generated for a course.

This limit is imposed to help avoid accidental excessive API usage and its associated cost rather than being a technical
limitation.
"""

AI_DISCLAIMER = (
    "This is an AI-generated voice, not a human, presenting AI-generated content that might be biased or inaccurate."
)
"""Disclaimer required by the [OpenAI usage policy](https://openai.com/policies/usage-policies/) and likely others.

This disclaimer is inserted as the first line in the course audio.
"""
