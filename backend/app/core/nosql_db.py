from http import client
from app.core.config import settings
from app.utils import create_user_default_configs
from odmantic import SyncEngine
from pymongo import MongoClient

client = MongoClient(host=str(settings.MONGODB_URI))
engine = SyncEngine(client=client, database=settings.MONGODB_DB)

def init_db(first_admin_id: str | None) -> None:
    from app.models.preference import Config
    from app.models.resume import PlainTextResume
    
    engine.configure_database([Config, PlainTextResume])
    
    if first_admin_id:
        create_user_default_configs(first_admin_id, engine)
