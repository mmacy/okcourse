import asyncio
from pathlib import Path

import streamlit as st

from okcourse import Course, OpenAIAsyncGenerator
from okcourse.constants import MAX_LECTURES
from okcourse.utils.log_utils import get_logger
from okcourse.utils.string_utils import get_duration_string_from_seconds


async def main():
    log = get_logger("streamlit")

    st.title("OK Courses Course Generator")

    # Initialize session state variables
    if "course" not in st.session_state:
        log.info("Initializing session state with new 'Course' instance...")
        st.session_state.course = Course()
    if "do_generate_outline" not in st.session_state:
        log.info("Initializing session state with outline generation flag set to 'False'...")
        st.session_state.do_generate_outline = False
    if "do_generate_course" not in st.session_state:
        log.info("Initializing session state with course generation flag set to 'False'...")
        st.session_state.do_generate_course = False

    course = st.session_state.course
    course.title = st.text_input("Enter the course topic:")
    course.settings.num_lectures = st.number_input(
        "Number of lectures:", min_value=1, max_value=MAX_LECTURES, value=20, step=1
    )
    course.settings.num_subtopics = st.number_input(
        "Number of subtopics per lecture:", min_value=1, max_value=10, value=4, step=1
    )

    generate_audio = st.checkbox("Generate MP3 audio file for course", value=False)
    generate_image = False

    if generate_audio:
        generate_image = st.checkbox("Generate cover image for audio file", value=False)

    generator = OpenAIAsyncGenerator(course)

    if generate_audio:
        course.settings.tts_voice = st.selectbox("Choose a voice for the course lecturer", options=generator.tts_voices)

    course.settings.output_directory = (
        Path(st.text_input("Output directory:", value=course.settings.output_directory)).expanduser().resolve()
    )

    if st.button("Generate outline") or st.session_state.do_generate_outline:
        if not course.title.strip():
            st.error("Enter a course topic.")

        try:
            with st.spinner("Generating course outline..."):
                st.session_state.do_generate_outline = False
                course = await generator.generate_outline(course)
                st.success("Course outline generated and ready for review.")
        except Exception as e:
            st.error(f"Failed to generate outline: {e}")
            log.error(f"Failed to generate outline: {e}")
            return

    # Display outline for review and allow regeneration
    if course.outline:
        st.write("## Course outline")
        st.write(str(course.outline))

        if st.button("Generate another outline"):
            course.outline = None
            st.session_state.do_generate_outline = True
            st.rerun()

        if st.button("Proceed with course generation"):
            st.session_state.do_generate_course = True

    # Generate Course Content
    if st.session_state.do_generate_course and course.outline:
        st.session_state.do_generate_course = False
        generator = OpenAIAsyncGenerator(course)

        try:
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
            st.write("## Generation details")
            st.json(course.generation_info.model_dump())

        except Exception as e:
            st.error(f"Failed to generate course: {e}")
            log.error(f"Failed to generate course: {e}")
            return


if __name__ == "__main__":
    asyncio.run(main())
