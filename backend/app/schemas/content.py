import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.content import WikiStatus


class WikiArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    slug: str = Field(min_length=3, max_length=260, pattern=r"^[a-z0-9-]+$")
    content_markdown: str = Field(min_length=1)
    category: str | None = Field(default=None, max_length=120)
    status: WikiStatus = WikiStatus.DRAFT


class WikiArticleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    slug: str | None = Field(default=None, min_length=3, max_length=260, pattern=r"^[a-z0-9-]+$")
    content_markdown: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, max_length=120)
    status: WikiStatus | None = None


class WikiArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firm_id: uuid.UUID
    author_user_id: uuid.UUID
    title: str
    slug: str
    content_markdown: str
    category: str | None
    status: WikiStatus
    published_at: datetime | None
