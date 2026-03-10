"""In-memory session state management for the web app."""

import logging
import time
import uuid
from dataclasses import dataclass, field

from okcourse import Course, OpenAIAsyncGenerator

from .log_capture import SessionLogHandler

SESSION_MAX_AGE_SECONDS = 7200  # 2 hours


@dataclass
class SessionState:
    """Holds all state for a single user session."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    course: Course = field(default_factory=Course)
    generator: OpenAIAsyncGenerator | None = None
    log_handler: SessionLogHandler = field(default_factory=SessionLogHandler)
    current_step: str = "configure"
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    generating: bool = False

    def touch(self) -> None:
        self.last_active = time.time()

    def attach_logger(self) -> None:
        """Attaches the session's log handler to the okcourse logger tree."""
        logger = logging.getLogger("okcourse")
        # Avoid duplicate handlers for this session
        for h in logger.handlers[:]:
            if h is self.log_handler:
                return
        formatter = logging.Formatter("%(message)s")
        self.log_handler.setFormatter(formatter)
        self.log_handler.setLevel(logging.INFO)
        logger.addHandler(self.log_handler)

    def detach_logger(self) -> None:
        """Removes the session's log handler from the okcourse logger tree."""
        logger = logging.getLogger("okcourse")
        for h in logger.handlers[:]:
            if h is self.log_handler:
                logger.removeHandler(h)


# Global session store — safe for asyncio single-threaded event loop
_sessions: dict[str, SessionState] = {}


def get_or_create_session(session_id: str | None) -> SessionState:
    """Returns an existing session or creates a new one."""
    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        session.touch()
        return session
    session = SessionState()
    _sessions[session.session_id] = session
    return session


def get_session_by_id(session_id: str) -> SessionState | None:
    """Returns a session by ID or None if not found."""
    return _sessions.get(session_id)


def cleanup_expired_sessions() -> int:
    """Removes sessions older than SESSION_MAX_AGE_SECONDS. Returns count removed."""
    now = time.time()
    expired = [
        sid for sid, state in _sessions.items()
        if now - state.last_active > SESSION_MAX_AGE_SECONDS
    ]
    for sid in expired:
        session = _sessions.pop(sid)
        session.detach_logger()
    return len(expired)
