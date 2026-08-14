import hashlib
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings


class LocalStorage:
    def __init__(self, settings: Settings) -> None:
        self.root = Path(settings.local_storage_path)
        self.max_size = settings.max_upload_size_bytes

    async def save(
        self, upload: UploadFile, *, firm_id: UUID, document_id: UUID
    ) -> tuple[str, int, str]:
        content = await upload.read(self.max_size + 1)
        if len(content) > self.max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large"
            )
        if not upload.content_type or upload.content_type not in {
            "application/pdf",
            "image/jpeg",
            "image/png",
            "text/plain",
        }:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Unsupported file type",
            )
            self._validate_content(upload.content_type, content)
        storage_key = f"{firm_id}/{document_id}/{Path(upload.filename or 'file').name}"
        target = self.root / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_key, len(content), hashlib.sha256(content).hexdigest()

    @staticmethod
    def _validate_content(content_type: str, content: bytes) -> None:
        signatures = {
            "application/pdf": b"%PDF-",
            "image/jpeg": b"\xff\xd8\xff",
            "image/png": b"\x89PNG\r\n\x1a\n",
        }
        signature = signatures.get(content_type)
        if signature and not content.startswith(signature):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="File content does not match its type",
            )
        if content_type == "text/plain":
            try:
                content.decode("utf-8")
            except UnicodeDecodeError as error:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Text file is not valid UTF-8",
                ) from error

    def read(self, storage_key: str) -> bytes:
        target = self.root / storage_key
        if not target.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        return target.read_bytes()

    def delete(self, storage_key: str) -> None:
        target = self.root / storage_key
        if target.is_file():
            target.unlink()
