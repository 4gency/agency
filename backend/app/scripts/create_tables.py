import logging

from sqlmodel import Session, SQLModel

from app.core.db import engine
from app.models.preference import Config as JobPreferences
from app.models.resume import PlainTextResume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create database tables from SQLModel classes."""
    logger.info("Creating tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Tables created")

    # Test if we can read the tables
    with Session(engine) as session:
        try:
            from sqlmodel import select

            # Test JobPreferences
            result = session.exec(select(JobPreferences).limit(1))
            result.first()
            logger.info("JobPreferences table verified")

            # Test PlainTextResume
            result = session.exec(select(PlainTextResume).limit(1))
            result.first()
            logger.info("PlainTextResume table verified")

            logger.info("All tables are working correctly")
        except Exception as e:
            logger.error(f"Error testing tables: {e}")


if __name__ == "__main__":
    create_tables()
