from api.core.config import settings
from langchain_chroma import Chroma
from api import llm
from .parse_data import get_document, get_documents
from .load_data import load_sample_navigation_data
from api import db, schema
from sqlmodel import Session
from api.core.config import settings


embeddings = llm.get_embeddings_model(model_name=settings.NAVIGATION_EMBEDDING_MODEL)


def get_vectorstore() -> Chroma:
    """
    Load the Chroma vector store.

    This function loads the Chroma vector store from the directory specified in
    the `CHROMA_PERSIST_DIRECTORY` setting.

    Returns:
        Chroma: A Chroma vector store instance.

    Raises:
        Exception: If the vector store cannot be loaded.
    """
    try:
        vectordb = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            embedding_function=embeddings,
            collection_name="Navigation_Collection",
        )
    except Exception as e:
        print(f"Failed to load Chroma due to: {e}")
        raise Exception(f"Could not load Chroma!")
    return vectordb


def ensure_vectorstore_exists() -> None:
    """
    Ensure that the Chroma vector store exists.

    This function checks if the vector store can be loaded from the persisted
    directory. If it can't, or if it's empty, it calls `create_vector_store`
    to create a new one.
    """
    try:
        vectorstore = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            embedding_function=embeddings,
            collection_name="Navigation_Collection",
        )
        document_count = len(vectorstore.get()["documents"])
        assert document_count != 0
        print(
            f"Chroma database loaded from {settings.CHROMA_PERSIST_DIRECTORY} with {document_count} documents"
        )
    except Exception as e:
        print(
            f"Could not load Chroma database from {settings.CHROMA_PERSIST_DIRECTORY} {e}"
        )
        create_vector_store()


def create_vector_store() -> None:
    """
    Create the Chroma vector store and populate the SQL database.

    This function loads the sample navigation data, creates documents from it,
    and then creates a new Chroma vector store. It also populates the SQL
    database with the intent information, including the Chroma IDs.
    """
    print("Creating Chroma database")
    sample_navigation_intents = load_sample_navigation_data()
    if len(sample_navigation_intents) == 0:
        print("No navigation data was loaded, databases will be empty!")
        return

    print(f"Creating Intents ({len(sample_navigation_intents)})")
    documents = get_documents(navigation_intents=sample_navigation_intents)
    print(f"Created {len(documents)} Intents")

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        collection_name="Navigation_Collection",
    )
    print(f"Saved Chroma database at {settings.CHROMA_PERSIST_DIRECTORY}")

    chroma_ids = vectorstore.get()["ids"]
    for intent, chroma_id in zip(sample_navigation_intents, chroma_ids):
        intent["chroma_id"] = chroma_id

    session = Session(db.engine)

    insert_count = 0
    for intent in sample_navigation_intents:
        try:
            intent = schema.IntentCreate(**intent)
            db.create_intent_db(session=session, intent=intent)
            insert_count += 1
        except Exception as e:
            print(f"Failed to insert Intent due to: {e}")

    print(f"Added {insert_count} Intents to Database")


def insert_intent(intent: schema.IntentCreate) -> str:
    """
    Insert a single intent into the vector store.

    This function takes an intent, creates a document from it, and adds it to
    the Chroma vector store.

    Args:
        intent (schema.IntentCreate): The intent to insert.

    Returns:
        str: The Chroma ID of the inserted intent.
    """
    document = get_document(navigation_intent=intent)
    vectorstore = Chroma.from_documents(
        documents=[document],
        embedding=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        collection_name="Navigation_Collection",
    )
    print(f"Added Document to Chroma database")
    chroma_id = vectorstore.get()["ids"][-1]
    return chroma_id


def delete_intent(chroma_id: str):
    """
    Delete an intent from the vector store.

    This function deletes an intent from the Chroma vector store based on its
    Chroma ID.

    Args:
        chroma_id (str): The Chroma ID of the intent to delete.
    """
    vectorstore = Chroma(
        persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
        embedding_function=embeddings,
        collection_name="Navigation_Collection",
    )
    vectorstore.delete(ids=[chroma_id])
    print(f"Deleted document with Chroma ID: {chroma_id}")
