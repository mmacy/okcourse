# --8<-- [start:full_openaiasyncgenerator]
import asyncio
from okcourse import Course, OpenAIAsyncGenerator


async def main() -> None:
    """Use the OpenAIAsyncGenerator to generate a complete course."""

    # Create a course and initialize the generator
    course = Course(title="From AGI to ASI: Paperclips, Gray Goo, and You")
    generator = OpenAIAsyncGenerator(course)

    # Generate all course content - these make calls to the OpenAI API
    course = await generator.generate_outline(course)
    course = await generator.generate_lectures(course)
    course = await generator.generate_image(course)
    course = await generator.generate_audio(course)

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
