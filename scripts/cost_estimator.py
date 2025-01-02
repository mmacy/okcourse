# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "flask",
#     "pandas",
#     "tiktoken",
# ]
# ///

import os
import json
from flask import Flask, request, jsonify, render_template_string
from pandas import DataFrame
import tiktoken

app = Flask(__name__)

# Initialize the tiktoken encoder
encoding = tiktoken.get_encoding("o200k_base")

DARK_MODE_CSS_JS = """
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background-color: var(--bg-color, white);
        color: var(--text-color, black);
    }
    h1 {
        text-align: center;
        margin-top: 20px;
    }
    form, .content {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 30px auto;
    }
    label, input, button {
        font-size: 16px;
        margin: 10px;
    }
    button {
        padding: 10px 20px;
        border: none;
        cursor: pointer;
        background-color: var(--button-bg-color, #007BFF);
        color: var(--button-text-color, white);
        border-radius: 5px;
    }
    button:hover {
        background-color: var(--button-hover-bg-color, #0056b3);
    }
    .toggle-dark-mode {
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: var(--button-bg-color, #007BFF);
        color: var(--button-text-color, white);
        border: none;
        border-radius: 5px;
        padding: 10px;
        cursor: pointer;
    }
    table {
        width: 90%;
        margin: 20px auto;
        border-collapse: collapse;
    }
    th, td {
        border: 1px solid var(--table-border-color, black);
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: var(--table-header-bg-color, #007BFF);
        color: var(--table-header-text-color, white);
    }
    tr:nth-child(even) {
        background-color: var(--table-row-bg-color, #f2f2f2);
    }
    tr:nth-child(odd) {
        background-color: var(--table-alt-row-bg-color, white);
    }
</style>
<script>
    const toggleDarkMode = () => {
        const isDarkMode = document.body.classList.toggle("dark-mode");
        document.documentElement.style.setProperty('--bg-color', isDarkMode ? '#121212' : 'white');
        document.documentElement.style.setProperty('--text-color', isDarkMode ? '#e0e0e0' : 'black');
        document.documentElement.style.setProperty('--button-bg-color', isDarkMode ? '#333333' : '#007BFF');
        document.documentElement.style.setProperty('--button-hover-bg-color', isDarkMode ? '#555555' : '#0056b3');
        document.documentElement.style.setProperty('--button-text-color', isDarkMode ? 'white' : 'white');
        document.documentElement.style.setProperty('--table-border-color', isDarkMode ? '#444444' : 'black');
        document.documentElement.style.setProperty('--table-header-bg-color', isDarkMode ? '#333333' : '#007BFF');
        document.documentElement.style.setProperty('--table-header-text-color', isDarkMode ? 'white' : 'white');
        document.documentElement.style.setProperty('--table-row-bg-color', isDarkMode ? '#1e1e1e' : '#f2f2f2');
        document.documentElement.style.setProperty('--table-alt-row-bg-color', isDarkMode ? '#2a2a2a' : 'white');
        localStorage.setItem("darkMode", isDarkMode ? "enabled" : "disabled");
    };

    const applyDarkMode = () => {
        const darkMode = localStorage.getItem("darkMode");
        if (darkMode === "enabled") {
            document.body.classList.add("dark-mode");
            document.documentElement.style.setProperty('--bg-color', '#121212');
            document.documentElement.style.setProperty('--text-color', '#e0e0e0');
            document.documentElement.style.setProperty('--button-bg-color', '#333333');
            document.documentElement.style.setProperty('--button-hover-bg-color', '#555555');
            document.documentElement.style.setProperty('--button-text-color', 'white');
            document.documentElement.style.setProperty('--table-border-color', '#444444');
            document.documentElement.style.setProperty('--table-header-bg-color', '#333333');
            document.documentElement.style.setProperty('--table-header-text-color', 'white');
            document.documentElement.style.setProperty('--table-row-bg-color', '#1e1e1e');
            document.documentElement.style.setProperty('--table-alt-row-bg-color', '#2a2a2a');
        }
    };

    document.addEventListener("DOMContentLoaded", applyDarkMode);
</script>
"""


@app.route("/")
def index():
    """Homepage for the application."""
    return render_template_string(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>JSON Directory Analyzer</title>
            {DARK_MODE_CSS_JS}
        </head>
        <body>
            <button class="toggle-dark-mode" onclick="toggleDarkMode()">Toggle Dark Mode</button>
            <h1>JSON Directory Analyzer</h1>
            <form action="/analyze" method="get">
                <label for="path">Enter the directory path:</label>
                <input type="text" id="path" name="path" value="~/.okcourse_files" size="50">
                <button type="submit">Analyze</button>
            </form>
        </body>
        </html>
    """)


@app.route("/analyze")
def analyze():
    """Analyze JSON files in the specified directory."""
    path = request.args.get("path", "").strip()
    if not path:
        return jsonify({"error": "No path provided"}), 400

    # Expand user directory if provided
    expanded_path = os.path.expanduser(path)

    if not os.path.exists(expanded_path) or not os.path.isdir(expanded_path):
        return jsonify({"error": f"Invalid directory path: {expanded_path}"}), 400

    json_files = [f for f in os.listdir(expanded_path) if f.endswith(".json")]
    if not json_files:
        return jsonify({"error": "No JSON files found in the directory"}), 404

    statistics = []
    for json_file in json_files:
        file_path = os.path.join(expanded_path, json_file)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

                # Extract prompts from the JSON
                system_prompts = [
                    data.get("text_model_system_prompt", ""),
                    data.get("text_model_outline_prompt", ""),
                    data.get("text_model_lecture_prompt", ""),
                    data.get("image_model_prompt", ""),
                ]

                # Extract details from the JSON
                lectures = data.get("lectures", [])
                outline = data.get("outline", {})
                topics = outline.get("topics", [])

                # Calculate metrics
                total_chars = sum(len(lecture.get("text", "")) for lecture in lectures)
                num_lectures = len(lectures)
                avg_chars_per_lecture = total_chars / num_lectures if num_lectures > 0 else 0

                outline_text = " ".join(topic["title"] + " " + " ".join(topic.get("subtopics", [])) for topic in topics)
                outline_token_count = len(encoding.encode(outline_text))

                lecture_text = " ".join(lecture.get("text", "") for lecture in lectures)
                lecture_token_count = len(encoding.encode(lecture_text))

                # Calculate total tokens and costs
                total_tokens = outline_token_count + lecture_token_count
                estimated_text_cost = (total_tokens / 1_000_000) * 10.00  # Text rate: $10 per 1M tokens
                estimated_tts_cost = (total_chars / 1_000_000) * 15.00  # TTS rate: $15 per 1M characters

                # Input tokens (sum of prompt tokens, outline, and lecture titles)
                prompt_tokens = sum(
                    len(encoding.encode(lecture.get("title", ""))) + len(encoding.encode(outline_text))
                    for lecture in lectures
                )
                # Add system prompts token counts dynamically
                system_prompt_tokens = sum(len(encoding.encode(prompt)) for prompt in system_prompts)
                input_token_count = prompt_tokens + system_prompt_tokens

                # Estimated input cost
                estimated_input_cost = (input_token_count / 1_000_000) * 2.50  # Input rate: $2.50 per 1M tokens

                # Total cost
                estimated_total_cost = estimated_text_cost + estimated_tts_cost + estimated_input_cost

                statistics.append(
                    {
                        "file_name": json_file,
                        "title": data.get("title", "N/A"),
                        "num_topics": len(topics),
                        "num_lectures": num_lectures,
                        "total_chars": total_chars,
                        "avg_chars_per_lecture": round(avg_chars_per_lecture, 2),
                        "outline_token_count": outline_token_count,
                        "lecture_token_count": lecture_token_count,
                        "total_token_count": total_tokens,
                        "estimated_text_cost_usd": round(estimated_text_cost, 2),
                        "estimated_tts_cost_usd": round(estimated_tts_cost, 2),
                        "input_token_count": input_token_count,
                        "estimated_input_cost_usd": round(estimated_input_cost, 2),
                        "estimated_total_cost_usd": round(estimated_total_cost, 2),
                    }
                )
        except (json.JSONDecodeError, KeyError):
            statistics.append({"file_name": json_file, "error": "Invalid JSON structure"})

    # Convert statistics to a DataFrame for better readability
    df = DataFrame(statistics)
    df["num_topics"] = df["num_topics"].astype(int, errors="ignore")
    df["num_lectures"] = df["num_lectures"].astype(int, errors="ignore")
    df["total_chars"] = df["total_chars"].astype(int, errors="ignore")
    html_table = df.to_html(index=False)

    return render_template_string(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Analysis Results</title>
            {DARK_MODE_CSS_JS}
        </head>
        <body>
            <button class="toggle-dark-mode" onclick="toggleDarkMode()">Toggle Dark Mode</button>
            <h1>Analysis Results</h1>
            <div class="content">
                <a href="/">Back to Home</a>
                <br><br>
                {html_table}
            </div>
        </body>
        </html>
    """)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
