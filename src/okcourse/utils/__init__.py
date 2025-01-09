"""Utility functions for the `okcourse` package.

The `utils` package contains various utility modules that provide commonly used functions throughout the `okcourse`
library. These modules cover a range of functionalities, including logging, string manipulation, type inspection, and
multimedia processing.

Modules included in this package:

- [`audio_utils`][okcourse.utils.audio_utils]: Functions for handling and combining audio data, including MP3 tagging
and album art application.
- [`log_utils`][okcourse.utils.log_utils]: Utilities for setting up logging and tracking execution time for profiling
purposes.
- [`string_utils`][okcourse.utils.string_utils]: Tools for processing and managing strings, including text splitting,
filename sanitization, and duration formatting.
- [`misc_utils`][okcourse.utils.misc_utils]: Functions for extracting literal values from types and class members,
useful for configuration and API interactions.

Typical usage involves importing the required utility functions in other modules of the `okcourse` package to perform
operations such as logging setup, text processing, or audio file handling. These functions are designed to simplify and
standardize common tasks within the project.

Example usage of utilities from this package:

```python
from utils.log_utils import get_logger
from utils.string_utils import sanitize_filename

logger = get_logger(__name__)
filename = sanitize_filename("Course Outline")
```
"""

__all__ = [
    "audio_utils",
    "log_utils",
    "string_utils",
    "misc_utils",
]
