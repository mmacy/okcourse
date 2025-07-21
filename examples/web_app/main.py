"""FastAPI Web Application for OKCourse

A REST API web application that provides endpoints for generating audiobook-style courses
using the OKCourse library. Features a simple web interface and real-time progress updates.
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from okcourse import Course, OpenAIAsyncGenerator
from okcourse.constants import MAX_LECTURES
from okcourse.generators.openai.openai_utils import AIModels, get_usable_models_async, tts_voices
from okcourse.prompt_library import PROMPT_COLLECTION
from okcourse.utils.log_utils import get_logger

app = FastAPI(
    title="OKCourse API",
    description="Generate audiobook-style courses with lectures on any topic",
    version="0.1.0"
)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

logger = get_logger("fastapi_app")

active_courses: Dict[str, Course] = {}

class CourseCreateRequest(BaseModel):
    title: str
    num_lectures: int = 4
    num_subtopics: int = 4
    prompt_style: str = "Academic course"
    text_model_outline: str = "gpt-4o-mini"
    text_model_lecture: str = "gpt-4o-mini"
    generate_image: bool = False
    generate_audio: bool = False
    tts_voice: Optional[str] = "alloy"
    output_directory: str = "~/courses"

class GenerationStep(BaseModel):
    step: str
    status: str
    message: str
    course_id: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/models")
async def get_models():
    """Get available AI models for text generation."""
    try:
        models = await get_usable_models_async()
        return {"text_models": models.text_models}
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voices")
async def get_voices():
    """Get available TTS voices."""
    return {"voices": tts_voices}

@app.get("/api/prompt-styles")
async def get_prompt_styles():
    """Get available course prompt styles."""
    styles = {prompt.description: prompt.description for prompt in PROMPT_COLLECTION}
    return {"styles": list(styles.keys())}

@app.post("/api/courses")
async def create_course(request: CourseCreateRequest):
    """Create a new course and return its ID."""
    try:
        course_id = str(uuid.uuid4())
        course = Course()
        course.title = request.title
        course.settings.num_lectures = min(request.num_lectures, MAX_LECTURES)
        course.settings.num_subtopics = request.num_subtopics
        
        prompt_options = {prompt.description: prompt for prompt in PROMPT_COLLECTION}
        if request.prompt_style in prompt_options:
            course.settings.prompts = prompt_options[request.prompt_style]
        
        course.settings.text_model_outline = request.text_model_outline
        course.settings.text_model_lecture = request.text_model_lecture
        course.settings.tts_voice = request.tts_voice
        course.settings.output_directory = Path(request.output_directory).expanduser().resolve()
        
        active_courses[course_id] = course
        
        return {
            "course_id": course_id,
            "title": course.title,
            "status": "created"
        }
    except Exception as e:
        logger.error(f"Failed to create course: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/courses/{course_id}")
async def get_course(course_id: str):
    """Get course details by ID."""
    if course_id not in active_courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = active_courses[course_id]
    return {
        "course_id": course_id,
        "title": course.title,
        "outline": course.outline.model_dump() if course.outline else None,
        "lectures": [lecture.model_dump() for lecture in course.lectures] if course.lectures else [],
        "generation_info": course.generation_info.model_dump() if course.generation_info else None,
        "settings": course.settings.model_dump()
    }

@app.post("/api/courses/{course_id}/generate-outline")
async def generate_outline(course_id: str):
    """Generate course outline."""
    if course_id not in active_courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    try:
        course = active_courses[course_id]
        generator = OpenAIAsyncGenerator(course)
        
        course = await generator.generate_outline(course)
        active_courses[course_id] = course
        
        return {
            "status": "completed",
            "outline": course.outline.model_dump() if course.outline else None
        }
    except Exception as e:
        logger.error(f"Failed to generate outline for course {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/courses/{course_id}/generate-lectures")
async def generate_lectures(course_id: str):
    """Generate course lectures."""
    if course_id not in active_courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = active_courses[course_id]
    if not course.outline:
        raise HTTPException(status_code=400, detail="Course outline must be generated first")
    
    try:
        generator = OpenAIAsyncGenerator(course)
        
        course = await generator.generate_lectures(course)
        active_courses[course_id] = course
        
        return {
            "status": "completed",
            "lectures": [lecture.model_dump() for lecture in course.lectures]
        }
    except Exception as e:
        logger.error(f"Failed to generate lectures for course {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/courses/{course_id}/generate-image")
async def generate_image(course_id: str):
    """Generate course cover image."""
    if course_id not in active_courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = active_courses[course_id]
    if not course.outline:
        raise HTTPException(status_code=400, detail="Course outline must be generated first")
    
    try:
        generator = OpenAIAsyncGenerator(course)
        
        course = await generator.generate_image(course)
        active_courses[course_id] = course
        
        image_path = course.generation_info.image_file_path
        return {
            "status": "completed",
            "image_path": str(image_path) if image_path else None,
            "image_exists": image_path.exists() if image_path else False
        }
    except Exception as e:
        logger.error(f"Failed to generate image for course {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/courses/{course_id}/generate-audio")
async def generate_audio(course_id: str):
    """Generate course audio."""
    if course_id not in active_courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    course = active_courses[course_id]
    if not course.lectures:
        raise HTTPException(status_code=400, detail="Course lectures must be generated first")
    
    try:
        generator = OpenAIAsyncGenerator(course)
        
        course = await generator.generate_audio(course)
        active_courses[course_id] = course
        
        audio_path = course.generation_info.audio_file_path
        return {
            "status": "completed",
            "audio_path": str(audio_path) if audio_path else None,
            "audio_exists": audio_path.exists() if audio_path else False
        }
    except Exception as e:
        logger.error(f"Failed to generate audio for course {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/courses/{course_id}/progress")
async def stream_progress(course_id: str):
    """Stream real-time progress updates for course generation."""
    if course_id not in active_courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    async def generate_progress():
        """Generate Server-Sent Events for progress updates."""
        course = active_courses[course_id]
        
        while True:
            try:
                status_data = {
                    "course_id": course_id,
                    "has_outline": course.outline is not None,
                    "has_lectures": len(course.lectures) > 0,
                    "lecture_count": len(course.lectures),
                    "has_image": (course.generation_info.image_file_path is not None and 
                                course.generation_info.image_file_path.exists()) if course.generation_info else False,
                    "has_audio": (course.generation_info.audio_file_path is not None and 
                                course.generation_info.audio_file_path.exists()) if course.generation_info else False,
                    "generation_info": course.generation_info.model_dump() if course.generation_info else None
                }
                
                yield f"data: {json.dumps(status_data)}\n\n"
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in progress stream: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: str):
    """Delete a course from memory."""
    if course_id not in active_courses:
        raise HTTPException(status_code=404, detail="Course not found")
    
    del active_courses[course_id]
    return {"status": "deleted", "course_id": course_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)