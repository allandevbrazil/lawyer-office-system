import asyncio

from app.seed import seed_demo_data


if __name__ == "__main__":
    asyncio.run(seed_demo_data())