"""Logging utilities for managing log output and tracking execution time in the `okcourse` package.

This module provides functions for setting up logging to both the console and optionally to a file,
retrieving package versions, and a context manager for tracking execution time for profiling purposes.
"""

import logging
import time
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def get_logger(
    source_name: str = "okcourse", level: int = logging.INFO, file_path: Path | None = None
) -> logging.Logger:
    """Enable logging to the console and optionally to a file for the specified source.

    You typically will get the name of the source module or function by calling `__name__` in the source.

    Args:
        source_name: The source (module, method, etc.) that will pass log event messages to this logger.
        level: The logging level to set for the logger.
        file_path: The path to a file where logs will be written. If not provided, logs are written only to the console.

    Examples:

    Get the logger for a module and then set up a couple log events:

    ```python
    # This is the do_things.py module
    from log_utils import get_logger

    # Get the private logger instance for the do_things module
    _log = get_logger(__name__)

    # Then use the logger elsewhere in the module to log events
    def do_a_thing():
        _log.info("About to do a thing...")
        thing.doer.do(thing)
        _log.info("Did the thing.")
    ```
    """
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s][%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler_name = f"{source_name}_console_handler"
    file_handler_name = f"{source_name}_file_handler"

    # The first call to getLogger() with a new source name creates a new logger instance for that source
    logger = logging.getLogger(source_name)
    logger.setLevel(level)
    # logger.propagate = False  # Prevents messages from propagating to the root logger

    if console_handler_name not in (h.name for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.set_name(f"{source_name}_console_handler")
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if file_path and file_handler_name not in (h.name for h in logger.handlers) and file_path:
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True)
        file_handler = logging.FileHandler(str(file_path))
        file_handler.set_name(f"{source_name}_file_handler")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_top_level_version(package_name: str) -> str:
    """Retrieve the version of the specified top-level package.

    Args:
        package_name (str): The name of the top-level package.

    Returns:
        str: The version of the package.

    Raises:
        PackageNotFoundError: If the package is not found.
    """
    try:
        return version(package_name)
    except PackageNotFoundError as e:
        raise RuntimeError(f"Package '{package_name}' is not installed.") from e


@contextmanager
def time_tracker(target_object: object, attribute_name: str):
    """A [`contextmanager`][contextlib.contextmanager] that tracks elapsed time and stores it in the specified attribute of the target object.

    Wrap your long-running operation with the `time_tracker` context manager and pass it the object and the name of the
    attribute on the object you want to store the elapsed time in.

    Args:
        target_object: The object where the elapsed time should be recorded.
        attribute_name: The name of the attribute on the given target object where the elapsed time should be stored.

    Examples:

    Record time elapsed generating a course's outline in the course's
    [`CourseGenerationInfo`][okcourse.models.CourseGenerationInfo]:

    ```python
    async def generate_outline(self, course: Course) -> Course:
        with time_tracker(course.generation_info, "outline_generation_elapsed"):
            # Long-running operation here
        return course
    ```
    """
    start_time = time.perf_counter()
    yield  # Execution passes back to the caller
    elapsed_time = time.perf_counter() - start_time
    if hasattr(target_object, attribute_name):
        setattr(target_object, attribute_name, elapsed_time)
    else:
        raise AttributeError(f"Attribute '{attribute_name}' not found in {target_object.__class__.__name__}.")
