"""Custom logging handler that captures okcourse log records for streaming to clients via SSE."""

import logging
from collections import deque


class SessionLogHandler(logging.Handler):
    """A logging handler that buffers log records in a deque for per-session progress reporting.

    Attach an instance to the `okcourse` logger tree. The SSE endpoint reads from
    the deque and streams messages to the client.
    """

    def __init__(self, maxlen: int = 500):
        super().__init__()
        self.records: deque[str] = deque(maxlen=maxlen)
        self._read_index = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.records.append(msg)
        except Exception:
            self.handleError(record)

    def get_new_messages(self) -> list[str]:
        """Returns messages added since the last call to this method."""
        all_records = list(self.records)
        new = all_records[self._read_index:]
        self._read_index = len(all_records)
        return new

    def reset(self) -> None:
        """Clears all buffered messages and resets the read index."""
        self.records.clear()
        self._read_index = 0
