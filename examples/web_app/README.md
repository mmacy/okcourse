# OKCourse FastAPI Web Application

A modern web application built with FastAPI that provides a REST API and web interface for generating audiobook-style courses using the OKCourse library.

## Features

- **REST API**: Complete HTTP API for course generation workflow
- **Web Interface**: Clean, responsive web UI for course creation
- **Real-time Progress**: Step-by-step progress tracking during generation
- **Async Processing**: Efficient handling of AI API calls with async support
- **Interactive Documentation**: Auto-generated OpenAPI/Swagger docs

## Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API key set in `OPENAI_API_KEY` environment variable
- `uv` package manager

### Installation

1. Install dependencies:
   ```bash
   uv sync --all-groups
   ```

2. Set your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Running the Application

1. Start the FastAPI server:
   ```bash
   uv run uvicorn examples.web_app.main:app --reload
   ```

2. Open your browser and navigate to:
   - **Web Interface**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative API Docs**: http://localhost:8000/redoc

## Usage

### Web Interface

1. **Configure Course**: Enter course title, select models, and set generation options
2. **Generate Outline**: Create a structured course outline with lectures and subtopics
3. **Generate Lectures**: Produce full lecture content based on the outline
4. **Generate Image** (optional): Create a course cover image
5. **Generate Audio** (optional): Convert text to speech for the entire course

### REST API Endpoints

#### Course Management
- `POST /api/courses` - Create a new course
- `GET /api/courses/{course_id}` - Get course details
- `DELETE /api/courses/{course_id}` - Delete a course

#### Generation Steps
- `POST /api/courses/{course_id}/generate-outline` - Generate course outline
- `POST /api/courses/{course_id}/generate-lectures` - Generate lectures
- `POST /api/courses/{course_id}/generate-image` - Generate cover image
- `POST /api/courses/{course_id}/generate-audio` - Generate audio

#### Configuration
- `GET /api/models` - List available AI models
- `GET /api/voices` - List available TTS voices
- `GET /api/prompt-styles` - List available course styles

### Example API Usage

```python
import httpx

# Create a course
course_data = {
    "title": "Introduction to Machine Learning",
    "num_lectures": 3,
    "num_subtopics": 4,
    "prompt_style": "Academic course",
    "text_model_outline": "gpt-4o-mini",
    "text_model_lecture": "gpt-4o-mini"
}

async with httpx.AsyncClient() as client:
    # Create course
    response = await client.post("http://localhost:8000/api/courses", json=course_data)
    course_id = response.json()["course_id"]
    
    # Generate outline
    await client.post(f"http://localhost:8000/api/courses/{course_id}/generate-outline")
    
    # Generate lectures
    await client.post(f"http://localhost:8000/api/courses/{course_id}/generate-lectures")
```

## Architecture

### Backend (FastAPI)
- **main.py**: FastAPI application with REST endpoints
- **Static Files**: CSS and JavaScript assets served via FastAPI
- **Templates**: Jinja2 HTML templates for the web interface
- **Error Handling**: Comprehensive error handling with proper HTTP status codes

### Frontend
- **Vanilla JavaScript**: No framework dependencies for simplicity
- **Responsive Design**: Mobile-friendly CSS with flexbox and grid
- **Progress Tracking**: Visual step-by-step progress indicators
- **Error Handling**: User-friendly error messages and recovery

### Integration
- **OKCourse Library**: Direct integration with existing course generation logic
- **OpenAI APIs**: Async calls to OpenAI for text, image, and audio generation
- **File Management**: Automatic file handling and path management

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for OpenAI API access

### Default Settings
- **Server**: localhost:8000
- **Output Directory**: ~/courses
- **Default Models**: gpt-4o-mini for both outline and lectures
- **Default Voice**: alloy

## Troubleshooting

### Common Issues

1. **"Course not found" errors**: Course data is stored in memory and will be lost when the server restarts
2. **Model availability**: Not all OpenAI models may be available depending on your API plan
3. **File permissions**: Ensure the output directory is writable
4. **Rate limits**: OpenAI API rate limits may cause delays or failures

### Development

For development with auto-reload:
```bash
uv run uvicorn examples.web_app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Considerations

- Use a production WSGI server like Gunicorn
- Implement persistent storage instead of in-memory course storage
- Add authentication and authorization
- Configure proper logging and monitoring
- Use environment-specific configuration files

## Contributing

This web application follows the same development patterns as the main OKCourse library:
- Async-first design
- Type hints with Pydantic models
- Comprehensive error handling
- Clean separation of concerns

Feel free to extend the API endpoints, improve the UI, or add new features following these patterns.