from odmantic import SyncEngine
from pymongo import MongoClient

from app.core.config import settings

client = MongoClient(host=str(settings.MONGODB_URI))
engine = SyncEngine(client=client, database=settings.MONGODB_DB)


def init_db(first_admin_id: str | None) -> None:
    from app.models.preference import Config
    from app.models.resume import PlainTextResume

    engine.configure_database([Config, PlainTextResume])
