import os
import typing as typ
from sqlalchemy import create_engine
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session, Connection

_ENGINE = create_engine(
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
)

_Session = sessionmaker(bind=_ENGINE)


def _create_db_connection() -> typ.Tuple[Session, Connection]:
    """Create a new database connection."""
    session = _Session()
    conn = session.connection()
    return session, conn


@contextmanager
def get_db_connection():
    """Context manager for handling database transactions."""

    session, conn = _create_db_connection()

    try:
        yield conn
        session.commit()

    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
        raise e
    finally:
        session.close()
