from typing import Dict, List
from langchain_core.documents import Document
from api import schema


def get_documents(navigation_intents: List[Dict]) -> List[Document]:
    """
    Convert a list of navigation intents into a list of Document objects.

    This function takes a list of navigation intents, where each intent is a
    dictionary, and creates a `langchain_core.documents.Document` object for
    each intent, using the intent's description as the page content.

    Args:
        navigation_intents (List[Dict]): A list of navigation intents.

    Returns:
        List[Document]: A list of Document objects.
    """
    documents: List[Document] = []

    for intent in navigation_intents:
        try:
            doc = Document(page_content=intent["description"])
            documents.append(doc)
        except Exception as e:
            print(f"Create document failed due to: {e}")

    return documents


def get_document(navigation_intent: schema.IntentCreate) -> Document:
    """
    Convert a single navigation intent into a Document object.

    This function takes a `schema.IntentCreate` object and creates a
    `langchain_core.documents.Document` object from it, using the intent's
    description as the page content.

    Args:
        navigation_intent (schema.IntentCreate): The navigation intent.

    Returns:
        Document: The Document object.
    """
    try:
        doc = Document(page_content=navigation_intent.description)
        return doc
    except Exception as e:
        print(f"Create document failed due to: {e}")
