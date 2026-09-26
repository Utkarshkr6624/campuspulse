from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    """Provider-agnostic binary object storage."""

    @abstractmethod
    def save(self, key: str, data: bytes) -> str:
        """Persist bytes under key. Returns the storage key (never a client path)."""

    @abstractmethod
    def open(self, key: str) -> Path:
        """Return a readable local path for processing. Callers must not expose it."""

    @abstractmethod
    def read(self, key: str) -> bytes:
        """Read object bytes."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete object if it exists."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        ...
