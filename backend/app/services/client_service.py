from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Case, Client, User, UserRole
from app.schemas.client import ClientCreate, ClientUpdate


class ClientService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def require_staff(self, current_user: User) -> None:
        if current_user.role not in {UserRole.MASTER, UserRole.FUNCIONARIO}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")

    async def list_clients(self, current_user: User, search: str | None) -> list[Client]:
        query = select(Client).where(Client.firm_id == current_user.firm_id)
        if current_user.role == UserRole.CLIENTE:
            query = query.where(Client.user_id == current_user.id)
        else:
            self.require_staff(current_user)
        if search:
            query = query.where(Client.name.ilike(f"%{search}%"))
        return list((await self.session.scalars(query.order_by(Client.name))).all())

    async def create_client(self, payload: ClientCreate, current_user: User) -> Client:
        self.require_staff(current_user)
        client = Client(firm_id=current_user.firm_id, **payload.model_dump())
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def update_client(
        self, client_id: UUID, payload: ClientUpdate, current_user: User
    ) -> Client:
        self.require_staff(current_user)
        client = await self.session.scalar(
            select(Client).where(Client.id == client_id, Client.firm_id == current_user.firm_id)
        )
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(client, field, value)
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def delete_client(self, client_id: UUID, current_user: User) -> None:
        self.require_staff(current_user)
        client = await self.session.scalar(
            select(Client).where(Client.id == client_id, Client.firm_id == current_user.firm_id)
        )
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        linked_case = await self.session.scalar(select(Case.id).where(Case.client_id == client.id).limit(1))
        if linked_case:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Client has linked cases and cannot be deleted; set it as inactive instead",
            )
        await self.session.execute(delete(Client).where(Client.id == client.id))
        await self.session.commit()
