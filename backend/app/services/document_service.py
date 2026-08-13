import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import Client, Document, User, UserRole
from app.services.storage_service import LocalStorage


class DocumentService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.storage = LocalStorage(settings)

    async def list_documents(self, current_user: User) -> list[Document]:
        query = select(Document).where(
            Document.firm_id == current_user.firm_id, Document.deleted_at.is_(None)
        )
        if current_user.role == UserRole.CLIENTE:
            query = query.join(Client, Client.id == Document.client_id).where(
                Client.user_id == current_user.id, Document.visibility == "CLIENT"
            )
        return list((await self.session.scalars(query.order_by(Document.uploaded_at.desc()))).all())

    async def upload(
        self,
        upload: UploadFile,
        current_user: User,
        client_id: uuid.UUID | None,
        case_id: uuid.UUID | None,
        visibility: str,
    ) -> Document:
        if current_user.role == UserRole.CLIENTE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
        if not client_id and not case_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Context required"
            )
        if visibility not in {"INTERNAL", "CLIENT"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid visibility"
            )
        document = Document(
            firm_id=current_user.firm_id,
            client_id=client_id,
            case_id=case_id,
            uploaded_by=current_user.id,
            file_name=upload.filename or "file",
            storage_key="pending",
            mime_type=upload.content_type or "application/octet-stream",
            size_bytes=0,
            checksum="pending",
            visibility=visibility,
            uploaded_at=datetime.now(UTC),
        )
        self.session.add(document)
        await self.session.flush()
        storage_key, size_bytes, checksum = await self.storage.save(
            upload, firm_id=current_user.firm_id, document_id=document.id
        )
        document.storage_key = storage_key
        document.size_bytes = size_bytes
        document.checksum = checksum
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def get_document(self, document_id: uuid.UUID, current_user: User) -> Document:
        documents = await self.list_documents(current_user)
        document = next((item for item in documents if item.id == document_id), None)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    async def delete_document(self, document_id: uuid.UUID, current_user: User) -> None:
        if current_user.role == UserRole.CLIENTE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
        document = await self.get_document(document_id, current_user)
        document.deleted_at = datetime.now(UTC)
        await self.session.commit()
        self.storage.delete(document.storage_key)
