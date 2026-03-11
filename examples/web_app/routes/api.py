"""JSON API endpoints for models, voices, progress SSE, and file downloads."""

import asyncio
import io
import logging
import re
from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import FileResponse, Response, StreamingResponse
from fpdf import FPDF

from okcourse import Course
from okcourse.generators.openai.openai_utils import get_voices_for_model

from ..dependencies import get_cached_models
from ..session import get_session_by_id

router = APIRouter(prefix="/api")

log = logging.getLogger(__name__)

# Common Unicode characters that LLMs produce, mapped to Latin-1-safe replacements
_UNICODE_REPLACEMENTS = {
    "\u2014": "--",   # em dash
    "\u2013": "-",    # en dash
    "\u2018": "'",    # left single curly quote
    "\u2019": "'",    # right single curly quote
    "\u201c": '"',    # left double curly quote
    "\u201d": '"',    # right double curly quote
    "\u2026": "...",  # ellipsis
    "\u2022": "-",    # bullet
    "\u2012": "-",    # figure dash
    "\u2015": "--",   # horizontal bar
    "\u2032": "'",    # prime
    "\u2033": '"',    # double prime
    "\u00a0": " ",    # non-breaking space
    "\u200b": "",     # zero-width space
    "\u200c": "",     # zero-width non-joiner
    "\u200d": "",     # zero-width joiner
    "\ufeff": "",     # byte order mark
}


def _sanitize_for_latin1(text: str) -> str:
    """Replaces common Unicode characters with Latin-1-safe equivalents.

    Characters that have no known mapping are replaced with '?'.
    """
    for char, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _ascii_safe_filename(title: str | None) -> str:
    """Returns an ASCII-safe filename stem derived from the course title."""
    name = (title or "").strip().replace(" ", "_").lower()
    name = re.sub(r"[^a-z0-9_\-]", "", name)
    return name or "course"


@router.get("/models")
async def get_models(models=Depends(get_cached_models)):
    """Returns available AI models grouped by type."""
    return {
        "text_models": models.text_models,
        "image_models": models.image_models,
        "speech_models": models.speech_models,
    }


@router.get("/voices/{tts_model}")
async def get_voices(tts_model: str):
    """Returns voices compatible with the given TTS model."""
    return {"voices": get_voices_for_model(tts_model)}


@router.get("/prompt-styles")
async def get_prompt_styles():
    """Returns available course prompt styles."""
    from okcourse.prompt_library import PROMPT_COLLECTION

    return [{"description": p.description, "index": i} for i, p in enumerate(PROMPT_COLLECTION)]


@router.get("/progress")
async def progress_stream(session_id: str | None = Cookie(default=None)):
    """SSE endpoint that streams log messages for the current session."""

    async def event_generator():
        if not session_id:
            yield "data: No session\n\n"
            return

        session = get_session_by_id(session_id)
        if not session:
            yield "data: Session not found\n\n"
            return

        # Stream until generation completes
        while True:
            messages = session.log_handler.get_new_messages()
            for msg in messages:
                yield f"data: {msg}\n\n"

            if not session.generating:
                yield "event: done\ndata: complete\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _build_course_pdf(course: Course) -> bytes:
    """Builds a PDF document from the course content and returns it as bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    title = _sanitize_for_latin1(course.title or "Untitled Course")

    # Title page
    pdf.add_page()
    pdf.set_font("Helvetica", size=24, style="B")
    pdf.ln(60)
    pdf.multi_cell(0, 12, title, align="C")
    pdf.ln(10)
    if course.outline:
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 8, f"{len(course.outline.topics)} lectures", align="C")

    # Outline
    if course.outline:
        pdf.add_page()
        pdf.set_font("Helvetica", size=18, style="B")
        pdf.cell(0, 10, "Course outline", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        for topic in course.outline.topics:
            pdf.set_font("Helvetica", size=12, style="B")
            topic_title = _sanitize_for_latin1(f"Lecture {topic.number}: {topic.title}")
            pdf.cell(0, 8, topic_title, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=10)
            for subtopic in topic.subtopics:
                pdf.cell(10)
                pdf.cell(0, 6, _sanitize_for_latin1(f"-  {subtopic}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

    # Lectures
    if course.lectures:
        for lecture in course.lectures:
            pdf.add_page()
            pdf.set_font("Helvetica", size=16, style="B")
            lecture_heading = _sanitize_for_latin1(f"Lecture {lecture.number}: {lecture.title}")
            pdf.multi_cell(0, 10, lecture_heading)
            pdf.ln(4)
            pdf.set_font("Helvetica", size=11)
            for paragraph in lecture.text.split("\n\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    pdf.multi_cell(0, 6, _sanitize_for_latin1(paragraph))
                    pdf.ln(3)

    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


# Declared as a plain `def` so FastAPI runs it in a threadpool, avoiding blocking the event loop
# during PDF generation.
@router.get("/download/pdf")
def download_pdf(session_id: str | None = Cookie(default=None)):
    """Generates and serves a PDF of the course content."""
    session = get_session_by_id(session_id) if session_id else None
    if not session or not session.course.lectures:
        raise HTTPException(status_code=404, detail="No course content available")

    try:
        pdf_bytes = _build_course_pdf(session.course)
    except Exception:
        log.exception("PDF generation failed")
        raise HTTPException(status_code=500, detail="PDF generation failed")

    ascii_name = f"{_ascii_safe_filename(session.course.title)}.pdf"
    utf8_name = quote(f"{session.course.title or 'course'}.pdf")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}"},
    )


@router.get("/download/image")
def download_image(session_id: str | None = Cookie(default=None)):
    """Serves the generated course image for download."""
    session = get_session_by_id(session_id) if session_id else None
    if not session or not session.course.generation_info.image_file_path:
        raise HTTPException(status_code=404, detail="No image available")

    path = session.course.generation_info.image_file_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(path, filename=path.name, media_type="image/png")


@router.get("/download/audio")
def download_audio(session_id: str | None = Cookie(default=None)):
    """Serves the generated course audio for download."""
    session = get_session_by_id(session_id) if session_id else None
    if not session or not session.course.generation_info.audio_file_path:
        raise HTTPException(status_code=404, detail="No audio available")

    path = session.course.generation_info.audio_file_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(path, filename=path.name, media_type="audio/mpeg")
