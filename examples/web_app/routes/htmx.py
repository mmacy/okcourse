"""HTMX endpoints that return HTML partials for the wizard steps."""

import logging
import traceback

from fastapi import APIRouter, Depends, Form, Request

from okcourse import Course, CourseSettings, OpenAIAsyncGenerator
from okcourse.prompt_library import PROMPT_COLLECTION

from ..dependencies import get_session
from ..session import SessionState

router = APIRouter(prefix="/htmx")

log = logging.getLogger(__name__)


def _render(request: Request, template: str, context: dict):
    """Shortcut for rendering a Jinja2 template partial."""
    return request.app.state.templates.TemplateResponse(request, template, context)


def _render_error(request: Request, message: str):
    """Renders the error partial."""
    return _render(request, "partials/error.html", {"error_message": message})


@router.post("/session/configure")
async def configure_session(
    request: Request,
    session: SessionState = Depends(get_session),
    course_title: str = Form(...),
    text_model: str = Form("gpt-5.4"),
    image_model: str = Form("gpt-image-1.5"),
    tts_model: str = Form("gpt-4o-mini-tts"),
    tts_voice: str = Form("marin"),
    tts_instructions: str = Form(""),
    num_lectures: int = Form(4),
    num_subtopics: int = Form(4),
    prompt_style: int = Form(0),
    generate_image: bool = Form(False),
    generate_audio: bool = Form(False),
):
    """Creates or updates the session course from the config form, then starts outline generation."""
    prompts = PROMPT_COLLECTION[prompt_style] if 0 <= prompt_style < len(PROMPT_COLLECTION) else PROMPT_COLLECTION[0]

    settings = CourseSettings(
        prompts=prompts,
        num_lectures=num_lectures,
        num_subtopics=num_subtopics,
        text_model_outline=text_model,
        text_model_lecture=text_model,
        image_model=image_model,
        tts_model=tts_model,
        tts_voice=tts_voice,
        tts_instructions=tts_instructions if tts_instructions.strip() else None,
    )

    session.course = Course(title=course_title, settings=settings)
    # Store user preferences for image/audio generation
    request.app.state.session_prefs = getattr(request.app.state, "session_prefs", {})
    request.app.state.session_prefs[session.session_id] = {
        "generate_image": generate_image,
        "generate_audio": generate_audio,
    }

    session.current_step = "outline"
    session.log_handler.reset()

    return await generate_outline(request, session)


@router.post("/generate/outline")
async def generate_outline(
    request: Request,
    session: SessionState = Depends(get_session),
):
    """Generates a course outline and returns the outline partial."""
    if not session.course.title:
        return _render_error(request, "Please enter a course title first.")

    session.generating = True
    session.attach_logger()
    session.log_handler.reset()

    try:
        generator = OpenAIAsyncGenerator(session.course)
        session.generator = generator
        session.course = await generator.generate_outline(session.course)
        session.current_step = "outline"
    except Exception as e:
        log.error(f"Outline generation failed: {e}\n{traceback.format_exc()}")
        return _render_error(request, f"Outline generation failed: {e}")
    finally:
        session.generating = False

    return _render(request, "partials/outline.html", {"course": session.course})


@router.post("/generate/lectures")
async def generate_lectures(
    request: Request,
    session: SessionState = Depends(get_session),
):
    """Generates lectures and returns the lectures partial."""
    if not session.course.outline:
        return _render_error(request, "Generate an outline first.")

    session.generating = True
    session.attach_logger()
    session.log_handler.reset()

    try:
        generator = session.generator or OpenAIAsyncGenerator(session.course)
        session.generator = generator
        session.course = await generator.generate_lectures(session.course)
        session.current_step = "lectures"
    except Exception as e:
        log.error(f"Lecture generation failed: {e}\n{traceback.format_exc()}")
        return _render_error(request, f"Lecture generation failed: {e}")
    finally:
        session.generating = False

    prefs = getattr(request.app.state, "session_prefs", {}).get(session.session_id, {})
    return _render(request, "partials/lectures.html", {
        "course": session.course,
        "generate_image": prefs.get("generate_image", False),
        "generate_audio": prefs.get("generate_audio", False),
    })


@router.post("/generate/image")
async def generate_image(
    request: Request,
    session: SessionState = Depends(get_session),
):
    """Generates a cover image and returns the image partial."""
    if not session.course.outline:
        return _render_error(request, "Generate an outline first.")

    session.generating = True
    session.attach_logger()
    session.log_handler.reset()

    try:
        generator = session.generator or OpenAIAsyncGenerator(session.course)
        session.generator = generator
        session.course = await generator.generate_image(session.course)
        session.current_step = "image"
    except Exception as e:
        log.error(f"Image generation failed: {e}\n{traceback.format_exc()}")
        return _render_error(request, f"Image generation failed: {e}")
    finally:
        session.generating = False

    prefs = getattr(request.app.state, "session_prefs", {}).get(session.session_id, {})
    return _render(request, "partials/image.html", {
        "course": session.course,
        "generate_audio": prefs.get("generate_audio", False),
    })


@router.post("/generate/audio")
async def generate_audio(
    request: Request,
    session: SessionState = Depends(get_session),
):
    """Generates course audio and returns the audio partial."""
    if not session.course.lectures:
        return _render_error(request, "Generate lectures first.")

    session.generating = True
    session.attach_logger()
    session.log_handler.reset()

    try:
        generator = session.generator or OpenAIAsyncGenerator(session.course)
        session.generator = generator
        session.course = await generator.generate_audio(session.course)
        session.current_step = "audio"
    except Exception as e:
        log.error(f"Audio generation failed: {e}\n{traceback.format_exc()}")
        return _render_error(request, f"Audio generation failed: {e}")
    finally:
        session.generating = False

    return _render(request, "partials/audio.html", {"course": session.course})


@router.post("/summary")
async def show_summary(
    request: Request,
    session: SessionState = Depends(get_session),
):
    """Returns the summary partial with generation stats."""
    session.current_step = "summary"
    return _render(request, "partials/summary.html", {"course": session.course})
