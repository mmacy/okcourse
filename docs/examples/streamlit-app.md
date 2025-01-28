# Streamlit application - async

The [`streamlit_example.py`](https://github.com/mmacy/okcourse/blob/main/examples/streamlit_example.py) script is a single-file web application that uses [Streamlit](https://streamlit.io) and the [`OpenAIAsyncGenerator`][okcourse.generators.OpenAIAsyncGenerator] to generate courses.

![A screenshot of a Streamlit application titled "OK Courses Course Generator." The interface allows users to enter the course topic, specify the number of lectures and subtopics per lecture, and configure options such as generating MP3 audio files and cover images for the course. A dropdown menu allows selecting a voice for the course lecturer, and an output directory path is specified. A button labeled "Generate outline" is shown, and a green notification box states, "Course outline generated and ready for review." Below, a course outline is displayed, including the title "Intelligence Explosion To ASI: A Hypothetical Play-By-Play" and the first lecture with subtopics like "Historical Development of AI Systems" and "Human vs Machine Learning Capabilities.](../images/streamlit-example-01.png)

## Run the app

To run the Streamlit app locally:

1. Install [uv](https://docs.astral.sh/uv/).
1. Set the `OPENAI_API_KEY` environment variable with your API key.
1. Run `uv sync`.
1. Launch the app with `uv`:

    ```sh
    uv run streamlit run examples/streamlit_example.py
    ```

2. Navigate to the `localhost` URL shown in the command output.

    For example, in the following output, the URL is `http://localhost:8501`:

    ```console hl_lines="5"
    [user@host okcourse]$ uv run streamlit run examples/streamlit_example.py

    You can now view your Streamlit app in your browser.

    Local URL: http://localhost:8501
    Network URL: http://192.168.0.5:8501

    2025-01-10 22:38:58 [INFO][streamlit] Initializing session state with new 'Course' instance...
    2025-01-10 22:38:58 [INFO][streamlit] Initializing session state with outline generation flag set to 'False'...
    2025-01-10 22:38:58 [INFO][streamlit] Initializing session state with course generation flag set to 'False'...
    ```

## Streamlit example code listing

```python title="streamlit_example.py"
--8<-- "examples/streamlit_example.py"
```
