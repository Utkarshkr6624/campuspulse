from pathlib import Path

from app.core.exceptions import NotFoundError
from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Filesystem storage rooted at a configured directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Reject path traversal and absolute keys.
        if not key or key != Path(key).name or ".." in key or "/" in key or "\\" in key:
            raise ValueError("Invalid storage key.")
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root)):
            raise ValueError("Invalid storage key.")
        return path

    def save(self, key: str, data: bytes) -> str:
        path = self._resolve(key)
        path.write_bytes(data)
        return key

    def open(self, key: str) -> Path:
        path = self._resolve(key)
        if not path.is_file():
            raise NotFoundError("Stored file not found.")
        return path

    def read(self, key: str) -> bytes:
        return self.open(key).read_bytes()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.is_file():
            path.unlink()

    def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).is_file()
        except ValueError:
            return False
