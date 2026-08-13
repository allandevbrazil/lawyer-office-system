import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db_session
from app.models import User
from app.schemas.case import (
    CaseCreate,
    CaseEventCreate,
    CaseEventResponse,
    CaseResponse,
    CaseUpdate,
)
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=list[CaseResponse], summary="List cases in the authorized scope")
async def list_cases(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    search: str | None = Query(default=None),
) -> list[CaseResponse]:
    cases = await CaseService(session).list_cases(current_user)
    if search:
        normalized = search.casefold()
        cases = [case for case in cases if normalized in case.title.casefold()]
    return [CaseResponse.model_validate(case) for case in cases]


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CaseResponse:
    case = await CaseService(session).create_case(payload, current_user)
    return CaseResponse.model_validate(case)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CaseResponse:
    case = await CaseService(session).get_case(case_id, current_user)
    return CaseResponse.model_validate(case)


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    payload: CaseUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CaseResponse:
    case = await CaseService(session).update_case(case_id, payload, current_user)
    return CaseResponse.model_validate(case)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await CaseService(session).delete_case(case_id, current_user)


@router.post(
    "/{case_id}/events", response_model=CaseEventResponse, status_code=status.HTTP_201_CREATED
)
async def add_event(
    case_id: uuid.UUID,
    payload: CaseEventCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> CaseEventResponse:
    event = await CaseService(session).add_event(case_id, payload, current_user)
    return CaseEventResponse.model_validate(event)
