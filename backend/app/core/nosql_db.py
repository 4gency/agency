from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

from odmantic import AIOEngine

client = AsyncIOMotorClient(str(settings.MONGODB_URI))
engine = AIOEngine(client=client, database=settings.MONGODB_DB)

def init_db() -> None:
    pass # skip for now