from sqlmodel import Session, SQLModel, create_engine
from .models import Intent, Parameter, RequiredParameter, Response

# Database setup
sqlite_file_name = "./static/db/navigation_intents.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    """
    Create all tables in the database.

    This function creates the database tables based on the SQLModel metadata.
    It should be called once during the application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Get a database session.

    This function is a dependency that provides a database session for each
    request. It uses a context manager to ensure that the session is
    properly closed after the request is finished.
    """
    with Session(engine) as session:
        yield session
