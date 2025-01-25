import asyncio
from pathlib import Path
from logging import getLogger
import streamlit as st

from okcourse import Course, OpenAIAsyncGenerator
from okcourse.generators.openai.openai_utils import AIModels, get_usable_models_async, tts_voices
from okcourse.constants import MAX_LECTURES
from okcourse.prompt_library import PROMPT_COLLECTION
from okcourse.utils.log_utils import get_logger
from okcourse.utils.text_utils import get_duration_string_from_seconds


async def main():
    """OK Courses Course Generator

    This Streamlit application creates a course based on user-provided settings and a selected custom prompt. It can:
    1. Generate a course outline and allow regeneration until the user is satisfied.
    2. Generate the course lectures, allowing repeated regeneration of lectures until accepted.
    3. Generate a cover image (optionally), allowing repeated regeneration of the image until accepted.
    4. (Optionally) Generate TTS audio for the final course.

    ---
    **Features**
    - Multiple AI model choices for outline and lecture generation.
    - Optional cover image creation.
    - Optional TTS audio generation.

    Use the **"Generate outline"** button to first produce the outline.
    Once satisfied, press **"Proceed with course generation"** to generate or regenerate lectures.
    If specified, cover images are also generated with repeated acceptance/regeneration.
    Finally, audio is generated (if chosen) and a summary of all generation data is displayed.
    """

    if "logger" not in st.session_state:
        st.session_state.logger = get_logger("streamlit")

    log = st.session_state.logger

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

    # Flags to track when the user has accepted (or repeatedly regenerated) certain outputs
    if "lectures_done" not in st.session_state:
        st.session_state.lectures_done = False
    if "cover_image_done" not in st.session_state:
        st.session_state.cover_image_done = False

    course = st.session_state.course

    # Prompt options
    prompt_options = {prompt.description: prompt for prompt in PROMPT_COLLECTION}
    selected_prompt_name = st.selectbox("Course style", options=list(prompt_options.keys()))
    selected_prompt = prompt_options[selected_prompt_name]
    course.settings.prompts = selected_prompt

    # Course title
    course.title = st.text_input(
        "Course title", placeholder="Artificial Super Intelligence: Paperclips, Gray Goo, And You"
    )

    # AI model selection
    usable_model_options: AIModels = await get_usable_models_async()
    course.settings.text_model_outline = st.selectbox(
        "Outline model",
        options=usable_model_options.text_models,
        placeholder="Choose an AI model for outline generation",
    )

    course.settings.text_model_lecture = st.selectbox(
        "Lecture model",
        options=usable_model_options.text_models,
        placeholder="Choose an AI model for lecture generation",
    )

    # Number of lectures/subtopics
    course.settings.num_lectures = st.number_input(
        "Number of lectures:", min_value=1, max_value=MAX_LECTURES, value=4, step=1
    )
    course.settings.num_subtopics = st.number_input(
        "Number of subtopics per lecture:", min_value=1, max_value=10, value=4, step=1
    )

    # Checkboxes for generating image/audio
    generate_image = st.checkbox("Generate course image (PNG)", value=False)
    generate_audio = st.checkbox("Generate course audio (MP3)", value=False)

    generator = OpenAIAsyncGenerator(course)

    if generate_audio:
        course.settings.tts_voice = st.selectbox("Choose a voice for the course lecturer", options=tts_voices)

    # Output directory
    course.settings.output_directory = (
        Path(st.text_input("Output directory", value=course.settings.output_directory)).expanduser().resolve()
    )

    # Generate the outline
    if st.button("Generate outline") or st.session_state.do_generate_outline:
        if not course.title.strip():
            st.error("Enter a course title.")
        else:
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
            # Reset all acceptance flags and start the generation process
            st.session_state.do_generate_course = True
            st.session_state.lectures_done = False
            st.session_state.cover_image_done = False
            st.rerun()

    # Generate Course Content in steps
    if st.session_state.do_generate_course and course.outline:
        # We reuse the same generator object every step to keep consistent settings
        generator = OpenAIAsyncGenerator(course)

        # ---------------------
        # Step 1: Lectures
        # ---------------------
        if not st.session_state.lectures_done:
            # If no lectures exist, generate them
            if not course.lectures:
                try:
                    with st.spinner("Generating lectures..."):
                        course = await generator.generate_lectures(course)
                except Exception as e:
                    st.error(f"Failed to generate lectures: {e}")
                    log.error(f"Failed to generate lectures: {e}")
                    return

            # Display generated lectures
            st.write("## Lectures")
            for lecture in course.lectures:
                st.write(f"### Lecture {lecture.number}: {lecture.title}")
                st.write(lecture.text)

            col_lect1, col_lect2 = st.columns(2)
            if col_lect1.button("Regenerate Lectures"):
                course.lectures = []
                st.rerun()
            if col_lect2.button("Accept Lectures"):
                st.session_state.lectures_done = True
                st.rerun()

        # ---------------------
        # Step 2: Cover Image
        # ---------------------
        if st.session_state.lectures_done and generate_image and not st.session_state.cover_image_done:
            # If no cover image has been generated, do so
            if not course.generation_info.image_file_path or not course.generation_info.image_file_path.exists():
                try:
                    with st.spinner("Generating cover image..."):
                        course = await generator.generate_image(course)
                except Exception as e:
                    st.error(f"Failed to generate course image: {e}")
                    log.error(f"Failed to generate course image: {e}")
                    return

            # Display generated cover image
            img_path = course.generation_info.image_file_path
            if img_path and img_path.exists():
                st.image(str(img_path), caption="Cover Image")

            col_img1, col_img2 = st.columns(2)
            if col_img1.button("Regenerate Cover Image"):
                if img_path and img_path.exists():
                    img_path.unlink(missing_ok=True)
                course.generation_info.image_file_path = None
                st.rerun()

            if col_img2.button("Accept Cover Image"):
                st.session_state.cover_image_done = True
                st.rerun()

        # ---------------------
        # Step 3: Audio (if selected), then finalize
        # ---------------------
        # Only proceed to audio (and final summary) if either no cover image is requested or it is done
        if st.session_state.lectures_done and (not generate_image or st.session_state.cover_image_done):
            if generate_audio and (
                not course.generation_info.audio_file_path or not course.generation_info.audio_file_path.exists()
            ):
                try:
                    with st.spinner("Generating course audio..."):
                        course = await generator.generate_audio(course)
                except Exception as e:
                    st.error(f"Failed to generate course audio: {e}")
                    log.error(f"Failed to generate course audio: {e}")
                    return

            # If audio was generated, display it
            audio_path = course.generation_info.audio_file_path
            if generate_audio and audio_path and audio_path.exists():
                st.audio(str(audio_path), format="audio/mp3")

            # Final generation info
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

            # Reset flags to allow a fresh run if desired
            st.session_state.do_generate_course = False
            st.session_state.lectures_done = False
            st.session_state.cover_image_done = False


if __name__ == "__main__":
    asyncio.run(main())
