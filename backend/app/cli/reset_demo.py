import asyncio
import shutil
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text

from app.core.config import get_settings
from app.db import async_session_factory
from app.models import Activity
from app.seed import seed_demo_data, seed_initial_master

BUSINESS_TABLES = (
    "activities",
    "wiki_articles",
    "documents",
    "invoice_items",
    "invoices",
    "services",
    "case_events",
    "case_parties",
    "cases",
    "client_invitations",
    "clients",
    "password_reset_tokens",
    "refresh_tokens",
)


async def reset_demo() -> None:
    settings = get_settings()
    if settings.app_env != "demo" and not settings.demo_mode:
        raise RuntimeError("Demo reset requires APP_ENV=demo or DEMO_MODE=true")

    async with async_session_factory() as session:
        for table in BUSINESS_TABLES:
            await session.execute(text(f'DELETE FROM "{table}"'))
        await session.commit()

    shutil.rmtree(settings.local_storage_path, ignore_errors=True)
    await seed_initial_master()
    await seed_demo_data()


async def reset_demo_if_due() -> None:
    settings = get_settings()
    if not settings.demo_mode:
        return

    async with async_session_factory() as session:
        marker = await session.scalar(
            select(Activity)
            .where(Activity.action == "DEMO_RESET")
            .order_by(Activity.created_at.desc())
        )
    if marker and marker.created_at > datetime.now(UTC) - timedelta(
        days=settings.demo_reset_interval_days
    ):
        return
    await reset_demo()


if __name__ == "__main__":
    asyncio.run(reset_demo())
