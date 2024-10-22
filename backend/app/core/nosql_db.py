from http import client
from app.core.config import settings
from odmantic import SyncEngine
from pymongo import MongoClient

client = MongoClient(host=str(settings.MONGODB_URI))
engine = SyncEngine(client=client, database=settings.MONGODB_DB)

def init_db() -> None:
    from app.models.preference import Config
    from app.models.resume import PlainTextResume
    
    engine.configure_database([Config, PlainTextResume])
