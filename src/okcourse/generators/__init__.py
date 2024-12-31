"""The `generators` package includes course generators compatible with AI service provider APIs.

Examples:

```python
--8<-- "examples/snippets/async_openai_snippets.py:generate_course"
```

1. Generates a complete course—outline, lectures, audio, and cover image—using the
[`OpenAIAsyncGenerator`][okcourse.generators.OpenAIAsyncGenerator] for the given topic and with default
[`CourseSettings`][okcourse.models.CourseSettings].
"""

from .base import CourseGenerator
from .openai import OpenAIAsyncGenerator

__all__ = [
    "CourseGenerator",
    "OpenAIAsyncGenerator",
]
