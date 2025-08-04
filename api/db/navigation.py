from sqlmodel import Field, SQLModel


# SQLModel classes
class Intent(SQLModel, table=True):
    """
    Represents an intent in the database.

    Attributes:
        intent_id (int, optional): The primary key for the intent.
        intent_name (str): The name of the intent, which is unique and indexed.
        description (str, optional): A description of the intent.
        chroma_id (str, optional): The ID of the corresponding entry in ChromaDB.
    """
    intent_id: int | None = Field(default=None, primary_key=True)
    intent_name: str = Field(index=True, unique=True)
    description: str | None = Field(default=None)
    chroma_id: str | None = Field(default=None)


class Parameter(SQLModel, table=True):
    """
    Represents a parameter associated with an intent.

    Attributes:
        parameter_id (int, optional): The primary key for the parameter.
        intent_id (int): The foreign key linking to the intent.
        parameter_name (str): The name of the parameter, indexed for quick lookup.
        parameter_type (str): The data type of the parameter.
    """
    parameter_id: int | None = Field(default=None, primary_key=True)
    intent_id: int = Field(foreign_key="intent.intent_id")
    parameter_name: str = Field(index=True)
    parameter_type: str

    class Config:
        table_args = (
            {"sqlite_autoincrement": True},
            {"unique": ["intent_id", "parameter_name"]},
        )


class RequiredParameter(SQLModel, table=True):
    """
    Represents a required parameter for an intent.

    Attributes:
        required_id (int, optional): The primary key for the required parameter.
        intent_id (int): The foreign key linking to the intent.
        parameter_name (str): The name of the required parameter.
    """
    required_id: int | None = Field(default=None, primary_key=True)
    intent_id: int = Field(foreign_key="intent.intent_id")
    parameter_name: str

    class Config:
        table_args = (
            {"sqlite_autoincrement": True},
            {"unique": ["intent_id", "parameter_name"]},
        )


class Response(SQLModel, table=True):
    """
    Represents a response for an intent on a specific platform.

    Attributes:
        response_id (int, optional): The primary key for the response.
        intent_id (int): The foreign key linking to the intent.
        platform (str): The platform for which this response is intended.
        response_value (str): The actual response text.
    """
    response_id: int | None = Field(default=None, primary_key=True)
    intent_id: int = Field(foreign_key="intent.intent_id")
    platform: str
    response_value: str

    class Config:
        table_args = (
            {"sqlite_autoincrement": True},
            {"unique": ["intent_id", "platform"]},
        )
