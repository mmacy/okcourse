import asyncio
import aiofiles
from pathlib import Path

import streamlit as st
from okcourse import (
    TTS_VOICES,
    generate_course_audio_async,
    generate_course_image_async,
    generate_course_lectures_async,
    generate_course_outline_async,
    sanitize_filename,
    CourseOutline,
)


async def generate_course(
    outline: CourseOutline, do_generate_audio: bool = False, tts_voice: str = "nova", cover_art_path: Path = None
):
    st.write(f"Generating course text for {outline.title}...")
    course = await generate_course_lectures_async(outline)

    output_dir = Path.cwd() / "generated_okcourses"
    output_file_base = output_dir / sanitize_filename(course.title)
    output_file_mp3 = output_file_base.with_suffix(".mp3")
    output_file_json = output_file_base.with_suffix(".json")

    if do_generate_audio:
        st.write("Generating course audio...")
        course_audio_path = await generate_course_audio_async(course, output_file_mp3, tts_voice, cover_art_path)
        st.write(f"Course audio: {str(course_audio_path)}")

    async with aiofiles.open(output_file_json, "w", encoding="utf-8") as f:
        await f.write(course.model_dump_json(indent=2))
    st.write(f"Course JSON:  {str(output_file_json)}")


async def generate_course_outline(topic, num_lectures):
    st.write(f"Generating course outline with {num_lectures} lectures...")
    outline = await generate_course_outline_async(topic, num_lectures)
    return outline


def main():
    st.title("OK Course Maker")

    topic = st.text_input(
        "Course topic:",
        placeholder="Artificial Super Intelligence: Gray Goo, Paperclips, and Other Doomsday Scenarios",
    )
    num_lectures = st.number_input("Number of lectures in the course:", min_value=1, value=10, max_value=100)

    do_generate_audio = st.checkbox("Generate course audio in MP3 format?")
    tts_voice = "nova"
    if do_generate_audio:
        tts_voice = st.selectbox("Choose a voice for the lecturer", TTS_VOICES, index=TTS_VOICES.index(tts_voice))
        do_generate_cover_art = st.checkbox("Generate cover image for audio file?")

    if st.button("Generate outline"):
        if not topic:
            st.error("You must enter a course topic.")
        else:
            outline = asyncio.run(generate_course_outline(topic, num_lectures))
            st.session_state["outline"] = outline
            st.json(outline.model_dump_json(indent=2))

    if "outline" in st.session_state:
        outline = st.session_state["outline"]
        if st.button("Accept outline"):
            cover_art_path = (Path.cwd() / "generated_okcourses" / sanitize_filename(outline.title)).with_suffix(".png")
            st.write(f"Cover art path set to {cover_art_path}")
            if do_generate_cover_art:
                st.write("Generating cover image for course audio...")
                cover_image, cover_image_path = asyncio.run(generate_course_image_async(outline, cover_art_path))
                st.image(cover_image, caption=f"Cover image for '{outline.title}'", width=400)

            asyncio.run(generate_course(outline, do_generate_audio, tts_voice, cover_image_path))
            if do_generate_audio:
                st.audio(cover_art_path.with_suffix(".mp3"))


if __name__ == "__main__":
    main()
