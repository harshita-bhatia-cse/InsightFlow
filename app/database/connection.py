import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


load_dotenv(override = True)

database_url = os.getenv("DATABASE_URL")
print(
    "Database target:",
    database_url.rsplit("@", 1)[-1]
)
if not database_url:
    raise ValueError(
        "DATABASE_URL is missing. Add it to the .env file."
    )

engine = create_engine(database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()