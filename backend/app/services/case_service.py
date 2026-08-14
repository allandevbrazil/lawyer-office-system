import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Case, CaseEvent, Client, User, UserRole, UserStatus
from app.schemas.case import CaseCreate, CaseEventCreate, CaseUpdate


class CaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def require_staff(self, current_user: User) -> None:
        if current_user.role not in {UserRole.MASTER, UserRole.FUNCIONARIO}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")

    async def list_cases(self, current_user: User) -> list[Case]:
        query = select(Case).where(Case.firm_id == current_user.firm_id)
        if current_user.role == UserRole.CLIENTE:
            query = query.join(Client, Client.id == Case.client_id).where(
                Client.user_id == current_user.id
            )
        return list((await self.session.scalars(query.order_by(Case.opened_at.desc()))).all())

    async def create_case(self, payload: CaseCreate, current_user: User) -> Case:
        self.require_staff(current_user)
        client = await self.session.scalar(
            select(Client).where(
                Client.id == payload.client_id, Client.firm_id == current_user.firm_id
            )
        )
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        case = Case(
            firm_id=current_user.firm_id,
            client_id=payload.client_id,
            title=payload.title,
            description=payload.description,
            case_number=payload.case_number,
            court=payload.court,
            jurisdiction=payload.jurisdiction,
            case_type=payload.case_type,
            priority=payload.priority,
            opened_at=datetime.now(UTC),
        )
        self.session.add(case)
        await self.session.commit()
        await self.session.refresh(case)
        return case

    async def get_case(self, case_id: uuid.UUID, current_user: User) -> Case:
        query = select(Case).where(Case.id == case_id, Case.firm_id == current_user.firm_id)
        if current_user.role == UserRole.CLIENTE:
            query = query.join(Client, Client.id == Case.client_id).where(
                Client.user_id == current_user.id
            )
        case = await self.session.scalar(query)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return case

    async def update_case(
        self, case_id: uuid.UUID, payload: CaseUpdate, current_user: User
    ) -> Case:
        case = await self.get_case(case_id, current_user)
        self.require_staff(current_user)
        values = payload.model_dump(exclude_unset=True)
        responsible_user_id = values.get("responsible_user_id")
        if responsible_user_id is not None:
            responsible_user = await self.session.scalar(
                select(User).where(
                    User.id == responsible_user_id,
                    User.firm_id == current_user.firm_id,
                    User.role.in_([UserRole.MASTER, UserRole.FUNCIONARIO]),
                    User.status == UserStatus.ACTIVE,
                )
            )
            if not responsible_user:
                raise HTTPException(status_code=404, detail="Responsible user not found")
        for field, value in values.items():
            setattr(case, field, value)
        if case.status == "ARCHIVED" and case.closed_at is None:
            case.closed_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(case)
        return case

    async def delete_case(self, case_id: uuid.UUID, current_user: User) -> None:
        case = await self.get_case(case_id, current_user)
        self.require_staff(current_user)
        await self.session.execute(delete(Case).where(Case.id == case.id))
        await self.session.commit()

    async def add_event(
        self, case_id: uuid.UUID, payload: CaseEventCreate, current_user: User
    ) -> CaseEvent:
        case = await self.get_case(case_id, current_user)
        if current_user.role == UserRole.CLIENTE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
        if payload.visibility not in {"INTERNAL", "CLIENT"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid visibility"
            )
        event = CaseEvent(
            case_id=case.id,
            author_user_id=current_user.id,
            event_type=payload.event_type,
            title=payload.title,
            description=payload.description,
            occurred_at=payload.occurred_at,
            visibility=payload.visibility,
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event
