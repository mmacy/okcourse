"""Values that define constraints related to course content or its generation by course [`generators`][okcourse.generators].

These constraints are in some cases driven by policy, practical, or financial considerations rather than technical
limitations.

For example, [`MAX_LECTURES`][okcourse.constants.MAX_LECTURES] is intended to prevent accidental excessive API usage and
the potentially excessive cost incurred by it.

While you *could* modify these values at runtime, they're here in the `constants` module to encourage you to treat them
as such. At the very least, you should be wary of the implications of changing them.
"""

MAX_LECTURES: int = 100
"""Maximum number of lectures that may be generated for a course.

This limit is imposed to help avoid a surprise financial burden due to accidental excessive API usage rather than being
a technical limitation.
"""

AI_DISCLOSURE: str = (
    "This is an AI-generated voice, not a human, presenting AI-generated content that might be biased or inaccurate."
)
"""Disclosure required by the [OpenAI usage policy](https://openai.com/policies/usage-policies/) and likely other providers' policies.

This disclosure is inserted by the `okcourse` library as the opening line in all TTS-generated course audio files.
"""
