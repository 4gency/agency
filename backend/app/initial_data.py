import logging

from sqlmodel import Session

from app.core.db import engine, init_db
from app.core.nosql_db import init_db as nosql_init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)


def main() -> None:
    logger.info("Creating SQL initial data")
    init()
    logger.info("Initial SQL data created")
    
    logger.info("Creating NoSQL initial data")
    nosql_init_db()
    logger.info("Initial NoSQL data created")


if __name__ == "__main__":
    main()
