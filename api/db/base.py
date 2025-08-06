from sqlmodel import Session, SQLModel, create_engine
from .navigation import Intent, Parameter, RequiredParameter, Response
from langchain_community.utilities import SQLDatabase
from sqlmodel import Session
from api import db, rag


# Database setup
sqlite_file_name = "./static/db/database.db"
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
        
        
def populate_summarization_tables():
    session = Session(engine)
    sample_summarization_data = rag.load_sample_summarization_data()
    if len(sample_summarization_data) == 0:
        print("No summarization data was loaded, databases will be empty!")
        return
    try:
        inserted_stats = db.populate_db_from_json(json_data=sample_summarization_data, session=session)
        if len(inserted_stats.keys()) == 0:
            print("Summarization data already present")
        else:
            print(f"Populated Summarization tables {inserted_stats}")
    except Exception as e:
        print(f"Failed to initialize Summarization tables due to: {e}")
    
sqlite_db = SQLDatabase.from_uri(sqlite_url)
