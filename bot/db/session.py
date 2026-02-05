from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def init_db(database_url: str) -> None:
    engine = create_engine(database_url, future=True)
    SessionLocal.configure(bind=engine)
    from bot.db import models

    models.Base.metadata.create_all(bind=engine)
