import streamlit as st

from okcourse import NUM_LECTURES, format_time, run_generation

st.title("Lecture Series Generator")

topic = st.text_input("Enter lecture series topic", "")
num_lectures = st.number_input("Number of lectures", min_value=1, value=NUM_LECTURES)
generate_audio_file = st.checkbox("Generate MP3 audio", value=False)

if st.button("Generate lecture series"):
    if not topic.strip():
        st.error("Please enter a topic.")
        st.stop()
    with st.spinner("Generating lectures..."):
        results = run_generation(topic.strip(), num_lectures, generate_audio_file)
    st.write("Lecture series generation complete.")
    st.write(f"Lecture series text: {results['aggregate_path']}")
    st.write(f"Lecture series outline: {results['outline_path']}")
    if generate_audio_file:
        st.write(f"Lecture series audio: {results['audio_path']}")
    st.write(f"Total generation time: {format_time(results['total_time'])}")
