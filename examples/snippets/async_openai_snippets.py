# --8<-- [start:full_openaiasyncgenerator]
import asyncio
from okcourse import Course, OpenAIAsyncGenerator


async def main() -> None:
    """Use the OpenAIAsyncGenerator to generate a complete course."""

    # Create a course, configure its settings, and initialize the generator
    course = Course(title="From AGI to ASI: Paperclips, Gray Goo, and You")
    generator = OpenAIAsyncGenerator(course)

    # Generate all course content with - these call AI provider APIs
    course = await generator.generate_outline(course)
    course = await generator.generate_lectures(course)
    course = await generator.generate_image(course)
    course = await generator.generate_audio(course)

    # A Course is a Pydantic model, as are its nested models
    print(course.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
# --8<-- [end:full_openaiasyncgenerator]


async def generate_outline_example() -> Course:
    """Use the OpenAIAsyncGenerator to generate a course outline."""

    # --8<-- [start:generate_outline]
    course = Course(title="From AGI to ASI: Paperclips, Gray Goo, and You")
    generator = OpenAIAsyncGenerator(course)
    course = await generator.generate_outline(course)
    # --8<-- [end:generate_outline]

    return course


async def generate_course_example() -> Course:
    """Use the OpenAIAsyncGenerator to generate a course outline."""

    # --8<-- [start:generate_course]
    course = Course(title="From AGI to ASI: Paperclips, Gray Goo, and You")
    generator = OpenAIAsyncGenerator(course)
    course = await generator.generate_course(course)  # (1)
    # --8<-- [end:generate_course]

    return course


async def generate_course_with_custom_settings() -> None:
    """Use the OpenAIAsyncGenerator to generate a complete course with custom settings."""

    # --8<-- [start:openaiasyncgenerator_custom_settings]
    course = Course(title="From AGI to ASI: Paperclips, Gray Goo, and You")  # (1)
    course.settings.num_lectures = 8  # (2)
    course.settings.output_directory = "~/my_awesome_ok_courses"  # (3)

    generator = OpenAIAsyncGenerator(course)  # (4)
    course = await generator.generate_outline(course)  # (5)
    course = await generator.generate_lectures(course)  # (6)
    course = await generator.generate_image(course)  # (7)
    course = await generator.generate_audio(course)  # (8)

    print(course.generation_info.model_dump_json(indent=2))  # (9)
    # --8<-- [end:full_openaiasyncgenerator_custom_settings]


if __name__ == "__main__":
    asyncio.run(main())
