"""Playwright tests for the okcourse web app.

These tests verify the UI loads correctly and the wizard flow works
by mocking the OpenAI generator to avoid real API calls.
"""

import sys
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from playwright.sync_api import Page, expect

from okcourse import Course, CourseLecture, CourseLectureTopic, CourseOutline
from okcourse.generators.openai import openai_utils

# Add project root to sys.path so `examples.web_app` is importable
_PROJECT_ROOT = str(Path(__file__).parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Port for the test server
TEST_PORT = 18932
TEST_URL = f"http://localhost:{TEST_PORT}"

# Mock AI models so the server can start without an OpenAI API key
_MOCK_MODELS = openai_utils.AIModels(
    text_models=["gpt-4o", "gpt-4o-mini", "gpt-5.4"],
    image_models=["dall-e-3", "dall-e-2", "gpt-image-1.5"],
    speech_models=["tts-1", "tts-1-hd", "gpt-4o-mini-tts"],
    other_models=[],
)


def _make_mock_course() -> Course:
    """Creates a Course with a pre-populated outline and lectures for mocking."""
    course = Course(title="Test Course on Testing")
    course.outline = CourseOutline(
        title="Test Course on Testing",
        topics=[
            CourseLectureTopic(
                number=1,
                title="Introduction to Testing",
                subtopics=["What is testing", "Why test", "Types of tests", "Test frameworks"],
            ),
            CourseLectureTopic(
                number=2,
                title="Advanced Testing Techniques",
                subtopics=["Mocking", "Integration tests", "End-to-end tests", "Performance tests"],
            ),
        ],
    )
    course.lectures = [
        CourseLecture(
            number=1,
            title="Introduction to Testing",
            subtopics=["What is testing", "Why test", "Types of tests", "Test frameworks"],
            text="This is the first lecture about testing \u2014 testing is essential for software quality.\n\n"
            "As Dijkstra once said, \u201cProgram testing can be used to show the presence of bugs, "
            "but never to show their absence.\u201d\n\n"
            "We\u2019ll explore three key areas\u2026 unit tests, integration tests, and end-to-end tests.",
        ),
        CourseLecture(
            number=2,
            title="Advanced Testing Techniques",
            subtopics=["Mocking", "Integration tests", "End-to-end tests", "Performance tests"],
            text="This is the second lecture about advanced testing techniques including mocking.",
        ),
    ]
    course.generation_info.outline_gen_elapsed_seconds = 1.5
    course.generation_info.outline_input_token_count = 100
    course.generation_info.outline_output_token_count = 200
    course.generation_info.lecture_gen_elapsed_seconds = 5.2
    course.generation_info.lecture_input_token_count = 500
    course.generation_info.lecture_output_token_count = 1000
    return course


@pytest.fixture(scope="module")
def server():
    """Starts the FastAPI server with mocked models for the test module."""
    import urllib.request

    # Pre-populate the models cache so no real OpenAI API call is made
    openai_utils._usable_models = _MOCK_MODELS

    from examples.web_app.main import app

    config = uvicorn.Config(app, host="127.0.0.1", port=TEST_PORT, log_level="warning")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()

    # Wait for server to be ready
    for _ in range(50):
        try:
            urllib.request.urlopen(TEST_URL)
            break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError("Test server failed to start")

    yield srv

    srv.should_exit = True
    thread.join(timeout=5)


@pytest.fixture()
def app_page(server, page: Page) -> Page:
    """Navigates to the app and returns the page."""
    page.goto(TEST_URL)
    return page


class TestPageLoad:
    """Tests that the main page loads with expected elements."""

    def test_page_title(self, app_page: Page):
        expect(app_page).to_have_title("okcourse")

    def test_header_visible(self, app_page: Page):
        expect(app_page.locator("header >> text=okcourse")).to_be_visible()

    def test_config_form_visible(self, app_page: Page):
        expect(app_page.locator("#course_title")).to_be_visible()

    def test_generate_button_visible(self, app_page: Page):
        expect(app_page.locator("#generate-btn")).to_be_visible()

    def test_prompt_style_dropdown(self, app_page: Page):
        select = app_page.locator("#prompt_style")
        expect(select).to_be_visible()
        options = select.locator("option")
        assert options.count() >= 1

    def test_num_lectures_default(self, app_page: Page):
        expect(app_page.locator("#num_lectures")).to_have_value("4")

    def test_num_subtopics_default(self, app_page: Page):
        expect(app_page.locator("#num_subtopics")).to_have_value("4")


class TestThemeToggle:
    """Tests the dark/light theme toggle."""

    def test_toggle_to_dark(self, app_page: Page):
        app_page.locator(".theme-toggle").click()
        expect(app_page.locator("html")).to_have_attribute("data-theme", "dark")

    def test_toggle_back_to_light(self, app_page: Page):
        toggle = app_page.locator(".theme-toggle")
        toggle.click()  # to dark
        toggle.click()  # back to light
        expect(app_page.locator("html")).to_have_attribute("data-theme", "light")


class TestModelSettings:
    """Tests the model settings details panel."""

    def test_model_settings_expandable(self, app_page: Page):
        details = app_page.locator("details:has(#text_model)")
        details.locator("summary").click()
        expect(app_page.locator("#text_model")).to_be_visible()
        expect(app_page.locator("#image_model")).to_be_visible()
        expect(app_page.locator("#tts_model")).to_be_visible()
        expect(app_page.locator("#tts_voice")).to_be_visible()

    def test_text_model_has_options(self, app_page: Page):
        app_page.locator("details:has(#text_model) >> summary").click()
        options = app_page.locator("#text_model >> option")
        assert options.count() >= 1

    def test_image_model_has_options(self, app_page: Page):
        app_page.locator("details:has(#image_model) >> summary").click()
        options = app_page.locator("#image_model >> option")
        assert options.count() >= 1


class TestVoiceUpdate:
    """Tests that voice dropdown updates when TTS model changes."""

    def test_voice_options_update_on_model_change(self, app_page: Page):
        app_page.locator("details:has(#tts_model) >> summary").click()

        tts_select = app_page.locator("#tts_model")
        voice_select = app_page.locator("#tts_voice")

        initial_count = voice_select.locator("option").count()

        # Select gpt-4o-mini-tts which has more voices
        tts_select.select_option("gpt-4o-mini-tts")
        # Wait for voice dropdown to update via fetch
        app_page.wait_for_timeout(500)
        new_count = voice_select.locator("option").count()
        # gpt-4o-mini-tts has more voices than classic models
        assert new_count >= initial_count


class TestWizardFlow:
    """Tests the wizard flow with mocked OpenAI calls."""

    def test_outline_generation(self, server, page: Page):
        """Tests that submitting the form generates and displays an outline."""
        mock_course = _make_mock_course()
        from okcourse.generators.openai.async_openai import OpenAIAsyncGenerator

        original_outline = OpenAIAsyncGenerator.generate_outline

        async def mock_generate_outline(self, course):
            course.outline = mock_course.outline
            course.generation_info.outline_gen_elapsed_seconds = 1.5
            course.generation_info.outline_input_token_count = 100
            course.generation_info.outline_output_token_count = 200
            return course

        try:
            OpenAIAsyncGenerator.generate_outline = mock_generate_outline

            page.goto(TEST_URL)
            page.locator("#course_title").fill("Test Course on Testing")
            page.locator("#generate-btn").click()

            page.wait_for_selector("#tab-outline h3", timeout=10000)

            expect(page.locator("#tab-outline")).to_contain_text("Test Course on Testing")
            expect(page.locator("#tab-outline")).to_contain_text("Introduction to Testing")
            expect(page.locator("#tab-outline")).to_contain_text("Advanced Testing Techniques")

            expect(page.locator("text=Regenerate outline")).to_be_visible()
            expect(page.locator("text=Accept and generate lectures")).to_be_visible()

            # Verify the Outline tab appeared in the tab bar
            expect(page.locator(".tab-bar >> text=Outline")).to_be_visible()
        finally:
            OpenAIAsyncGenerator.generate_outline = original_outline

    def test_lecture_generation(self, server, page: Page):
        """Tests that accepting an outline generates lectures."""
        mock_course = _make_mock_course()
        from okcourse.generators.openai.async_openai import OpenAIAsyncGenerator

        original_outline = OpenAIAsyncGenerator.generate_outline
        original_lectures = OpenAIAsyncGenerator.generate_lectures

        async def mock_generate_outline(self, course):
            course.outline = mock_course.outline
            course.generation_info.outline_gen_elapsed_seconds = 1.5
            course.generation_info.outline_input_token_count = 100
            course.generation_info.outline_output_token_count = 200
            return course

        async def mock_generate_lectures(self, course):
            course.lectures = mock_course.lectures
            course.generation_info.lecture_gen_elapsed_seconds = 5.2
            course.generation_info.lecture_input_token_count = 500
            course.generation_info.lecture_output_token_count = 1000
            return course

        try:
            OpenAIAsyncGenerator.generate_outline = mock_generate_outline
            OpenAIAsyncGenerator.generate_lectures = mock_generate_lectures

            page.goto(TEST_URL)
            page.locator("#course_title").fill("Test Course on Testing")
            page.locator("#generate-btn").click()

            page.wait_for_selector("text=Accept and generate lectures", timeout=10000)
            page.locator("text=Accept and generate lectures").click()

            page.wait_for_selector("#tab-lectures >> text=Lectures for:", timeout=10000)

            expect(page.locator("#tab-lectures")).to_contain_text("Lectures for: Test Course on Testing")
            expect(page.locator("#tab-lectures")).to_contain_text("Introduction to Testing")
            expect(page.locator("#tab-lectures")).to_contain_text("Advanced Testing Techniques")

            # Verify both tabs appeared
            expect(page.locator(".tab-bar >> text=Outline")).to_be_visible()
            expect(page.locator(".tab-bar >> text=Lectures")).to_be_visible()

            # Verify clicking Outline tab shows outline content
            page.locator(".tab-bar >> text=Outline").click()
            expect(page.locator("#tab-outline")).to_be_visible()
            expect(page.locator("#tab-outline")).to_contain_text("Introduction to Testing")
        finally:
            OpenAIAsyncGenerator.generate_outline = original_outline
            OpenAIAsyncGenerator.generate_lectures = original_lectures

    def test_summary_view(self, server, browser, page: Page):
        """Tests that the summary view shows generation stats."""
        mock_course = _make_mock_course()
        from okcourse.generators.openai.async_openai import OpenAIAsyncGenerator

        original_outline = OpenAIAsyncGenerator.generate_outline
        original_lectures = OpenAIAsyncGenerator.generate_lectures

        async def mock_generate_outline(self, course):
            course.outline = mock_course.outline
            course.generation_info.outline_gen_elapsed_seconds = 1.5
            course.generation_info.outline_input_token_count = 100
            course.generation_info.outline_output_token_count = 200
            return course

        async def mock_generate_lectures(self, course):
            course.lectures = mock_course.lectures
            course.generation_info.lecture_gen_elapsed_seconds = 5.2
            course.generation_info.lecture_input_token_count = 500
            course.generation_info.lecture_output_token_count = 1000
            return course

        try:
            OpenAIAsyncGenerator.generate_outline = mock_generate_outline
            OpenAIAsyncGenerator.generate_lectures = mock_generate_lectures

            # Use a fresh browser context to avoid cookie interference from prior tests
            ctx = browser.new_context()
            fresh_page = ctx.new_page()

            fresh_page.goto(TEST_URL)
            fresh_page.locator("#course_title").fill("Test Course on Testing")
            fresh_page.locator("#generate-btn").click()

            fresh_page.wait_for_selector("text=Accept and generate lectures", timeout=10000)
            fresh_page.locator("text=Accept and generate lectures").click()

            # Wait for lectures partial to load before clicking summary
            fresh_page.wait_for_selector("#tab-lectures >> text=Lectures for:", timeout=10000)

            fresh_page.locator("text=View summary").click()

            fresh_page.wait_for_selector("text=Generation summary", timeout=10000)

            expect(fresh_page.locator("#tab-summary")).to_contain_text("Generation summary")
            expect(fresh_page.locator("#tab-summary")).to_contain_text("Test Course on Testing")
            expect(fresh_page.locator("#tab-summary")).to_contain_text("Start a new course")

            # Verify all tabs are present and clickable
            expect(fresh_page.locator(".tab-bar >> text=Outline")).to_be_visible()
            expect(fresh_page.locator(".tab-bar >> text=Lectures")).to_be_visible()
            expect(fresh_page.locator(".tab-bar >> text=Summary")).to_be_visible()

            ctx.close()
        finally:
            OpenAIAsyncGenerator.generate_outline = original_outline
            OpenAIAsyncGenerator.generate_lectures = original_lectures


class TestFormValidation:
    """Tests form behavior."""

    def test_empty_title_prevented(self, app_page: Page):
        """HTML5 required attribute prevents submission without a title."""
        expect(app_page.locator("#course_title")).to_have_attribute("required", "")


class TestApiEndpoints:
    """Tests JSON API endpoints directly."""

    def test_models_endpoint(self, server, page: Page):
        response = page.request.get(f"{TEST_URL}/api/models")
        assert response.ok
        data = response.json()
        assert "text_models" in data
        assert "image_models" in data
        assert "speech_models" in data

    def test_voices_endpoint(self, server, page: Page):
        response = page.request.get(f"{TEST_URL}/api/voices/tts-1")
        assert response.ok
        data = response.json()
        assert "voices" in data
        assert "alloy" in data["voices"]

    def test_voices_gpt4o_endpoint(self, server, page: Page):
        response = page.request.get(f"{TEST_URL}/api/voices/gpt-4o-mini-tts")
        assert response.ok
        data = response.json()
        assert "voices" in data
        assert "ballad" in data["voices"]

    def test_prompt_styles_endpoint(self, server, page: Page):
        response = page.request.get(f"{TEST_URL}/api/prompt-styles")
        assert response.ok
        data = response.json()
        assert len(data) >= 1
        assert "description" in data[0]

    def test_pdf_download_no_content(self, server, page: Page):
        """PDF endpoint returns 404 when no course content exists."""
        response = page.request.get(f"{TEST_URL}/api/download/pdf")
        assert response.status == 404

    def test_pdf_download_with_content(self, server, browser):
        """PDF endpoint returns a PDF file when lectures have been generated."""
        from okcourse.generators.openai.async_openai import OpenAIAsyncGenerator

        mock_course = _make_mock_course()
        original_outline = OpenAIAsyncGenerator.generate_outline
        original_lectures = OpenAIAsyncGenerator.generate_lectures

        async def mock_generate_outline(self, course):
            course.outline = mock_course.outline
            return course

        async def mock_generate_lectures(self, course):
            course.lectures = mock_course.lectures
            return course

        try:
            OpenAIAsyncGenerator.generate_outline = mock_generate_outline
            OpenAIAsyncGenerator.generate_lectures = mock_generate_lectures

            ctx = browser.new_context()
            fresh_page = ctx.new_page()
            fresh_page.goto(TEST_URL)
            fresh_page.locator("#course_title").fill("Test Course on Testing")
            fresh_page.locator("#generate-btn").click()
            fresh_page.wait_for_selector("text=Accept and generate lectures", timeout=10000)
            fresh_page.locator("text=Accept and generate lectures").click()
            fresh_page.wait_for_selector("#tab-lectures >> text=Lectures for:", timeout=10000)

            response = fresh_page.request.get(f"{TEST_URL}/api/download/pdf")
            assert response.ok
            assert response.headers["content-type"] == "application/pdf"
            body = response.body()
            assert body[:5] == b"%PDF-"

            ctx.close()
        finally:
            OpenAIAsyncGenerator.generate_outline = original_outline
            OpenAIAsyncGenerator.generate_lectures = original_lectures

    def test_static_files_served(self, server, page: Page):
        response = page.request.get(f"{TEST_URL}/static/app.js")
        assert response.ok

        response = page.request.get(f"{TEST_URL}/static/style.css")
        assert response.ok


class TestPdfBuilder:
    """Unit tests for the PDF builder function and helpers."""

    def test_build_pdf_basic(self):
        """PDF builder produces valid PDF bytes from a course with lectures."""
        from examples.web_app.routes.api import _build_course_pdf

        course = _make_mock_course()
        pdf_bytes = _build_course_pdf(course)
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 100

    def test_build_pdf_unicode_content(self):
        """PDF builder handles em dashes, curly quotes, and ellipses without crashing."""
        from examples.web_app.routes.api import _build_course_pdf

        course = _make_mock_course()
        # Mock lectures already contain Unicode (em dashes, curly quotes, ellipses)
        pdf_bytes = _build_course_pdf(course)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_build_pdf_none_title(self):
        """PDF builder handles a None title gracefully."""
        from examples.web_app.routes.api import _build_course_pdf

        course = _make_mock_course()
        course.title = None
        pdf_bytes = _build_course_pdf(course)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_build_pdf_no_outline(self):
        """PDF builder works when course has lectures but no outline."""
        from examples.web_app.routes.api import _build_course_pdf

        course = _make_mock_course()
        course.outline = None
        pdf_bytes = _build_course_pdf(course)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_sanitize_for_latin1(self):
        """Unicode sanitizer replaces common LLM characters with ASCII equivalents."""
        from examples.web_app.routes.api import _sanitize_for_latin1

        assert _sanitize_for_latin1("hello \u2014 world") == "hello -- world"
        assert _sanitize_for_latin1("\u201cquoted\u201d") == '"quoted"'
        assert _sanitize_for_latin1("it\u2019s") == "it's"
        assert _sanitize_for_latin1("wait\u2026") == "wait..."
        # Characters with no mapping get replaced with '?'
        assert "?" in _sanitize_for_latin1("\u4e16\u754c")  # Chinese characters

    def test_ascii_safe_filename(self):
        """Filename helper produces ASCII-only names with fallback."""
        from examples.web_app.routes.api import _ascii_safe_filename

        assert _ascii_safe_filename("My Course Title") == "my_course_title"
        assert _ascii_safe_filename("Schr\u00f6dinger's Cat") == "schrdingers_cat"
        assert _ascii_safe_filename("") == "course"
        assert _ascii_safe_filename(None) == "course"
        assert _ascii_safe_filename("   ") == "course"
