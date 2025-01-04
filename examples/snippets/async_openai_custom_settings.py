import asyncio
from pathlib import Path
from okcourse import Course, OpenAIAsyncGenerator


async def main() -> None:
    """Use the OpenAIAsyncGenerator to generate a complete course with custom settings."""

    # --8<-- [start:openaiasyncgenerator_custom_settings]
    # Generate a course with a few custom settings
    course = Course(title="From AGI to ASI: Paperclips, Gray Goo, and You") # (1)!
    course.settings.num_lectures = 8 # (2)!
    course.settings.tts_voice = "nova" # (3)!
    course.settings.output_directory = Path("~/my_ok_courses") # (4)!

    generator = OpenAIAsyncGenerator(course) # (5)!
    course = await generator.generate_outline(course) # (6)!
    course = await generator.generate_lectures(course) # (7)!
    course = await generator.generate_image(course) # (8)!
    course = await generator.generate_audio(course) # (9)!

    print(
        course.generation_info.model_dump_json(indent=2) # (10)!
    )
    # --8<-- [end:openaiasyncgenerator_custom_settings]

    # Output:
    # {
    #   "generator_type": "okcourse.generators.openai.async_openai",
    #   "okcourse_version": "0.1.8",
    #   "input_token_count": 5466,
    #   "output_token_count": 6504,
    #   "tts_character_count": 37290,
    #   "outline_gen_elapsed_seconds": 4.1996187078766525,
    #   "lecture_gen_elapsed_seconds": 10.632696291897446,
    #   "image_gen_elapsed_seconds": 14.767505957745016,
    #   "audio_gen_elapsed_seconds": 50.358656249940395,
    #   "num_images_generated": 1,
    #   "audio_file_path": "~/my_ok_courses/from_agi_to_asi_paperclips_gray_goo_and_you.mp3",
    #   "image_file_path": "~/my_ok_courses/from_agi_to_asi_paperclips_gray_goo_and_you.png"
    # }

    # 1. Courses may be on any topic that doesn't run afoul of the AI service provider's content policy.
    # 2. Lectures form the core content of a course. More lectures means longer courses.
    # 3. If the AI service provider supports it, you can specify which voice to use for the lecture audio.
    # 4. This is where the course audio file (MP3), its cover image (PNG), and log file(s) are saved. All are optional.
    # 5. Coures generators use an AI service provider's API to generate course content. OpenAI is the first supported provider.
    # 6. The course outline defines the structure of the course and includes the titles and subtopics of its lectures.
    # 7. Based on the course outline, this method populates the text of each lecture in the course.
    # 8. To have AI generate album art for the audio file, call `generate_image()` before you generate the audio file (next line).
    # 9. This is the final step in the course generation process. It creates an MP3 file of the course's lectures read aloud by an AI-generated voice.
    # 10. The `Course` object is a Pydantic model - built-in support for (de)serialization for easier save/load!


    # --8<-- [end:openaiasyncgenerator_custom_settings_output]


if __name__ == "__main__":
    asyncio.run(main())
