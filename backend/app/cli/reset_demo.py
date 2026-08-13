import asyncio
import shutil

from sqlalchemy import text

from app.core.config import get_settings
from app.db import async_session_factory
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
    if settings.app_env != "demo":
        raise RuntimeError("Demo reset is allowed only when APP_ENV=demo")

    async with async_session_factory() as session:
        for table in BUSINESS_TABLES:
            await session.execute(text(f'DELETE FROM "{table}"'))
        await session.commit()

    shutil.rmtree(settings.local_storage_path, ignore_errors=True)
    await seed_initial_master()
    await seed_demo_data()


if __name__ == "__main__":
    asyncio.run(reset_demo())
