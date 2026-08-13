import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firm_id: uuid.UUID
    client_id: uuid.UUID | None
    case_id: uuid.UUID | None
    uploaded_by: uuid.UUID
    file_name: str
    mime_type: str
    size_bytes: int
    visibility: str
    folder: str | None
    uploaded_at: datetime
