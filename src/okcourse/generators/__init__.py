"""The `generators` package includes course generators compatible with APIs offered by different AI service providers.

## Available generators

- [`OpenAIAsyncGenerator`][okcourse.generators.openai.OpenAIAsyncGenerator]: An asynchronous course generator that uses
    OpenAI's models to generate course assets.

To use these classes, import them directly from this package.

## Examples

```python
from okcourse.generators import OpenAIAsyncGenerator

generator = OpenAIAsyncGenerator()
await generator.generate_course()
```
"""

from .base import CourseGenerator
from .openai import OpenAIAsyncGenerator

__all__ = [
    "CourseGenerator",
    "OpenAIAsyncGenerator",
]
