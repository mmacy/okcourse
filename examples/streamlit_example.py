import asyncio
from pathlib import Path

import streamlit as st

from okcourse import Course, OpenAIAsyncGenerator
from okcourse.utils.string_utils import get_duration_string_from_seconds


async def main():
    st.title("Course Generator with okcourse")

    course_title = st.text_input("Enter the course topic:")
    num_lectures = st.number_input("Number of lectures:", min_value=1, max_value=20, value=4, step=1)
    num_subtopics = st.number_input("Number of subtopics per lecture:", min_value=1, max_value=10, value=4, step=1)

    generate_audio = st.checkbox("Generate MP3 audio file for course", value=False)
    generate_image = False
    tts_voice = None
    tts_voices = []

    if generate_audio:
        generate_image = st.checkbox("Generate cover image for audio file", value=False)

    # Instantiate OpenAIAsyncGenerator to get available voices
    temp_course = Course(title=course_title)
    temp_generator = OpenAIAsyncGenerator(temp_course)
    tts_voices = temp_generator.tts_voices
    if generate_audio:
        tts_voice = st.selectbox("Choose a voice for the course lecturer", options=tts_voices)

    # Output directory
    default_output_directory = str(Path("~/.okcourse_files").expanduser().resolve())
    output_directory = st.text_input("Output directory:", value=default_output_directory)

    # Generate Course Button
    if st.button("Generate Course"):
        if not course_title.strip():
            st.error("Please enter a course topic.")
        else:
            # Create course and settings
            course = Course(title=course_title)
            course.settings.num_lectures = int(num_lectures)
            course.settings.num_subtopics = int(num_subtopics)
            course.settings.output_directory = Path(output_directory).expanduser().resolve()
            course.settings.log_to_file = True
            if generate_audio:
                course.settings.tts_voice = tts_voice

            generator = OpenAIAsyncGenerator(course)

            try:
                with st.spinner("Generating course outline..."):
                    course = await generator.generate_outline(course)
                    st.write("## Course Outline")
                    st.write(str(course.outline))

                regenerate = st.checkbox("Regenerate the outline", value=False)
                if regenerate:
                    st.warning("Click 'Generate Course' again to regenerate the outline.")
                    return

                with st.spinner("Generating lectures..."):
                    course = await generator.generate_lectures(course)
                    st.write("## Lectures")
                    for lecture in course.lectures:
                        st.write(f"### Lecture {lecture.number}: {lecture.title}")
                        st.write(lecture.text)

                if generate_image:
                    with st.spinner("Generating cover image..."):
                        course = await generator.generate_image(course)
                        image_path = course.generation_info.image_file_path
                        if image_path and image_path.exists():
                            st.image(str(image_path), caption="Cover Image")

                if generate_audio:
                    with st.spinner("Generating course audio..."):
                        course = await generator.generate_audio(course)
                        audio_path = course.generation_info.audio_file_path
                        if audio_path and audio_path.exists():
                            st.audio(str(audio_path), format="audio/mp3")

                # Display generation info
                total_time_seconds = (
                    course.generation_info.outline_gen_elapsed_seconds
                    + course.generation_info.lecture_gen_elapsed_seconds
                    + course.generation_info.image_gen_elapsed_seconds
                    + course.generation_info.audio_gen_elapsed_seconds
                )
                total_generation_time = get_duration_string_from_seconds(total_time_seconds)
                st.success(f"Course generated in {total_generation_time}.")
                st.write("## Generation Details")
                st.json(course.generation_info.model_dump())

            except Exception as e:
                st.error(f"An error occurred during course generation: {e}")
                return


if __name__ == "__main__":
    asyncio.run(main())
