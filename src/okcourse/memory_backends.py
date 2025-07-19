from __future__ import annotations

"""Prototype storage backends for holding generated course artifacts in memory."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict


class StorageBackend(ABC):
    """Abstract interface for storing generated artifacts."""

    @abstractmethod
    def save_bytes(self, path: Path, data: bytes) -> None:
        pass

    @abstractmethod
    def load_bytes(self, path: Path) -> bytes | None:
        pass


class FileSystemBackend(StorageBackend):
    """Store artifacts on disk using the normal filesystem."""

    def save_bytes(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def load_bytes(self, path: Path) -> bytes | None:
        if path.exists():
            return path.read_bytes()
        return None


class InMemoryBackend(StorageBackend):
    """Keep artifacts only in memory."""

    def __init__(self) -> None:
        self._storage: Dict[Path, bytes] = {}

    def save_bytes(self, path: Path, data: bytes) -> None:
        self._storage[path] = data

    def load_bytes(self, path: Path) -> bytes | None:
        return self._storage.get(path)

