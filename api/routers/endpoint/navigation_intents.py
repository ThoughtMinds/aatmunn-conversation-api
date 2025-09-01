from typing import Annotated, Dict, List, Optional
from fastapi import Depends, APIRouter, HTTPException, Query
from sqlmodel import Session
from api import schema, db, rag


router = APIRouter()

SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/intents/", response_model=schema.IntentResponse)
async def create_intent(
    intent: schema.IntentCreate, session: SessionDep
) -> schema.IntentResponse:
    """Create a new intent with associated parameters, required parameters, and responses.

    Args:
        intent (schema.IntentCreate): The intent data including name, description, parameters, required parameters, and responses.
        session (SessionDep): The database session dependency for executing queries.

    Returns:
        schema.IntentResponse: The created intent with its ID, name, description, parameters, required parameters, and responses.

    Raises:
        HTTPException: If there is a database error (e.g., unique constraint violation).
    """
    chroma_id = rag.insert_intent(intent=intent)
    intent.chroma_id = chroma_id
    return db.create_intent_db(intent, session)


@router.get("/intents/{intent_id}", response_model=schema.IntentResponse)
async def read_intent(intent_id: int, session: SessionDep) -> schema.IntentResponse:
    """Retrieve an intent by its ID, including its parameters, required parameters, and responses.

    Args:
        intent_id (int): The ID of the intent to retrieve.
        session (SessionDep): The database session dependency for executing queries.

    Returns:
        schema.IntentResponse: The intent data including ID, name, description, parameters, required parameters, and responses.

    Raises:
        HTTPException: If the intent with the specified ID is not found (404).
    """
    return db.read_intent_db(intent_id, session)


@router.get("/intents/", response_model=List[schema.IntentResponse])
async def read_intents(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[Optional[int], Query(le=100)] = None,
) -> List[schema.IntentResponse]:
    """Retrieve a paginated list of all intents with their parameters, required parameters, and responses.

    Args:
        session (SessionDep): The database session dependency for executing queries.
        offset (int, optional): The number of records to skip for pagination. Defaults to 0.
        limit (Optional[int], optional): The maximum number of records to return, capped at 100. Defaults to None (fetch all).

    Returns:
        List[schema.IntentResponse]: A list of intents, each including ID, name, description, parameters, required parameters, and responses.
    """
    return db.read_intents_db(session, offset, limit)


@router.delete("/intents/{intent_id}")
async def delete_intent(intent_id: int, session: SessionDep) -> Dict[str, bool]:
    """Delete an intent by its ID, including its associated parameters, required parameters, and responses.

    Args:
        intent_id (int): The ID of the intent to delete.
        session (SessionDep): The database session dependency for executing queries.

    Returns:
        Dict[str, bool]: A dictionary with a key 'ok' set to True indicating successful deletion.

    Raises:
        HTTPException: If the intent with the specified ID is not found (404).
    """
    chroma_id = db.delete_intent_db(intent_id, session)
    rag.delete_intent(chroma_id=chroma_id)
    return {"ok": True}


@router.put("/intents/{intent_id}", response_model=schema.IntentResponse)
async def update_intent(
    intent_id: int,
    intent_update: schema.IntentCreate,
    session: Session = Depends(db.get_session),
):
    """Update an existing intent by ID.

    Args:
        intent_id (int): The ID of the intent to update.
        intent_update (schema.IntentCreate): The updated intent data.
        session (Session): The database session.

    Returns:
        schema.IntentResponse: The updated intent data.

    Raises:
        HTTPException: If the intent is not found (404) or if there's a database error (400).
    """
    chroma_id, response = db.update_intent_db(intent_id, intent_update, session)
    rag.delete_intent(chroma_id=chroma_id)
    chroma_id = rag.insert_intent(intent=intent_update)
    db.update_intent_chroma_id_db(intent_id, chroma_id, session)
    return response


@router.get("/get_intent_count")
async def get_intent_count(session: SessionDep) -> Dict[str, int]:
    """
    Get the total number of intents in the database.

    Args:
        session (SessionDep): The database session dependency.

    Returns:
        Dict[str, int]: A dictionary with the key 'total_intents' and the count of intents.
    """
    intent_count = db.count_intents_db(session=session)
    return {"total_intents": intent_count}
