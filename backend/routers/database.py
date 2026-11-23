
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import make_url

# Load environment variables from the project root .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured. "
        "Please check the .env file."
    )

# Explicitly use Psycopg 3 for Neon/PostgreSQL. SQLite remains supported only
# for isolated local tests; production must provide a PostgreSQL URL.
database_url = make_url(DATABASE_URL)

if database_url.drivername in {"postgres", "postgresql"}:
    database_url = database_url.set(
        drivername="postgresql+psycopg"
    )

engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

if database_url.drivername.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}
    if database_url.database in {None, "", ":memory:"}:
        engine_options["poolclass"] = StaticPool

engine = create_engine(database_url, **engine_options)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
