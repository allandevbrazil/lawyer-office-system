import asyncio

from app.cli.reset_demo import reset_demo_if_due


if __name__ == "__main__":
    asyncio.run(reset_demo_if_due())