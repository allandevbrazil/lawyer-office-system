from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db_session
from app.core.security import hash_password
from app.models import FirmConfig, User, UserRole, UserStatus, WikiArticle, WikiStatus
from app.schemas.admin import FirmSettingsUpdate
from app.schemas.auth import StaffCreate, StaffUpdate, UserResponse
from app.schemas.content import WikiArticleCreate, WikiArticleResponse, WikiArticleUpdate

router = APIRouter(tags=["administration"])


@router.get("/staff", response_model=list[UserResponse])
async def list_staff(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[UserResponse]:
    if current_user.role not in {UserRole.MASTER, UserRole.FUNCIONARIO}:
        raise HTTPException(status_code=403, detail="Staff role required")
    users = list(
        (
            await session.scalars(
                select(User).where(
                    User.firm_id == current_user.firm_id,
                    User.role != UserRole.CLIENTE,
                    User.status != UserStatus.SUSPENDED,
                )
            )
        ).all()
    )
    return [UserResponse.model_validate(user) for user in users]


@router.post("/staff", response_model=UserResponse, status_code=201)
async def create_staff(payload: StaffCreate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> UserResponse:
    if current_user.role != UserRole.MASTER:
        raise HTTPException(status_code=403, detail="Master role required")
    if payload.role != UserRole.FUNCIONARIO:
        raise HTTPException(status_code=422, detail="Only staff users can be created here")
    existing = await session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(firm_id=current_user.firm_id, email=str(payload.email).lower(), full_name=payload.full_name, password_hash=hash_password(payload.password), role=payload.role, status=UserStatus.ACTIVE, phone=payload.phone)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/staff/{user_id}", response_model=UserResponse)
async def update_staff(user_id: str, payload: StaffUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> UserResponse:
    if current_user.role != UserRole.MASTER:
        raise HTTPException(status_code=403, detail="Master role required")
    user = await session.scalar(select(User).where(User.id == user_id, User.firm_id == current_user.firm_id, User.role != UserRole.MASTER))
    if not user:
        raise HTTPException(status_code=404, detail="Staff member not found")
    values = payload.model_dump(exclude_unset=True)
    if values.get("role") == UserRole.MASTER:
        raise HTTPException(status_code=422, detail="Master role cannot be assigned here")
    if "password" in values:
        user.password_hash = hash_password(values.pop("password"))
    if "email" in values:
        values["email"] = str(values["email"]).lower()
    for field, value in values.items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/staff/{user_id}", status_code=204)
async def delete_staff(user_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> None:
    if current_user.role != UserRole.MASTER:
        raise HTTPException(status_code=403, detail="Master role required")
    user = await session.scalar(select(User).where(User.id == user_id, User.firm_id == current_user.firm_id, User.role != UserRole.MASTER))
    if not user:
        raise HTTPException(status_code=404, detail="Staff member not found")
    user.status = UserStatus.SUSPENDED
    await session.commit()


@router.get("/wiki/articles", response_model=list[WikiArticleResponse])
async def list_wiki(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[WikiArticleResponse]:
    if current_user.role == UserRole.CLIENTE:
        raise HTTPException(status_code=403, detail="Staff role required")
    query = select(WikiArticle).where(WikiArticle.firm_id == current_user.firm_id)
    if current_user.role != UserRole.MASTER:
        query = query.where(WikiArticle.status == WikiStatus.PUBLISHED)
    articles = list((await session.scalars(query.order_by(WikiArticle.title))).all())
    return [WikiArticleResponse.model_validate(article) for article in articles]


@router.post("/wiki/articles", response_model=WikiArticleResponse, status_code=201)
async def create_wiki(
    payload: WikiArticleCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> WikiArticleResponse:
    if current_user.role not in {UserRole.MASTER, UserRole.FUNCIONARIO}:
        raise HTTPException(status_code=403, detail="Staff role required")
    article = WikiArticle(
        firm_id=current_user.firm_id,
        author_user_id=current_user.id,
        title=payload.title,
        slug=payload.slug,
        content_markdown=payload.content_markdown,
        category=payload.category,
        status=payload.status,
        published_at=datetime.now(UTC) if payload.status == WikiStatus.PUBLISHED else None,
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)
    return WikiArticleResponse.model_validate(article)


@router.patch("/wiki/articles/{article_id}", response_model=WikiArticleResponse)
async def update_wiki(article_id: str, payload: WikiArticleUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> WikiArticleResponse:
    if current_user.role not in {UserRole.MASTER, UserRole.FUNCIONARIO}:
        raise HTTPException(status_code=403, detail="Staff role required")
    article = await session.scalar(select(WikiArticle).where(WikiArticle.id == article_id, WikiArticle.firm_id == current_user.firm_id))
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(article, field, value)
    article.published_at = datetime.now(UTC) if article.status == WikiStatus.PUBLISHED else None
    await session.commit()
    await session.refresh(article)
    return WikiArticleResponse.model_validate(article)


@router.delete("/wiki/articles/{article_id}", status_code=204)
async def delete_wiki(article_id: str, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> None:
    if current_user.role != UserRole.MASTER:
        raise HTTPException(status_code=403, detail="Master role required")
    article = await session.scalar(select(WikiArticle).where(WikiArticle.id == article_id, WikiArticle.firm_id == current_user.firm_id))
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    await session.delete(article)
    await session.commit()


@router.get("/settings/firm")
async def get_firm_settings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    if current_user.role != UserRole.MASTER:
        raise HTTPException(status_code=403, detail="Master role required")
    config = await session.scalar(
        select(FirmConfig).where(FirmConfig.firm_id == current_user.firm_id)
    )
    if not config:
        raise HTTPException(status_code=404, detail="Firm settings not found")
    return {
        "id": str(config.id),
        "firm_id": str(config.firm_id),
        "legal_name": config.legal_name,
        "trade_name": config.trade_name,
        "tax_id": config.tax_id,
        "email": config.email,
        "phone": config.phone,
        "logo_url": config.logo_url,
        "timezone": config.timezone,
        "currency": config.currency,
    }


@router.patch("/settings/firm")
async def update_firm_settings(payload: FirmSettingsUpdate, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    if current_user.role != UserRole.MASTER:
        raise HTTPException(status_code=403, detail="Master role required")
    config = await session.scalar(select(FirmConfig).where(FirmConfig.firm_id == current_user.firm_id))
    if not config:
        raise HTTPException(status_code=404, detail="Firm settings not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
    await session.commit()
    return await get_firm_settings(current_user, session)
