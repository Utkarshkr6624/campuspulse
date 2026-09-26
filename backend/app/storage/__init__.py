from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend


@lru_cache
def get_storage() -> StorageBackend:
    backend = settings.document_storage_backend.lower().strip()
    if backend == "local":
        root = Path(settings.document_storage_path)
        if not root.is_absolute():
            from app.core.config import BACKEND_DIR

            root = BACKEND_DIR / root
        return LocalStorageBackend(root)
    raise RuntimeError(f"Unsupported document storage backend: {backend}")
