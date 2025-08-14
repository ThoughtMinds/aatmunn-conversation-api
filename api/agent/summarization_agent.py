from api import db, llm, tools
from typing import Dict
from pydantic import BaseModel
from json import dumps
from api.core.logging_config import logger
from sqlmodel import Session


class ToolCall(BaseModel):
    name: str
    parameters: Dict


chat_model = llm.get_ollama_chat_model()

tool_list = [
    tools.summarization.fetch_employee_by_id_db,
    tools.summarization.list_employees_by_skill_level_db,
    tools.summarization.list_employees_by_performance_rating_db,
    tools.summarization.list_employees_by_skill_db,
    tools.summarization.list_employees_by_department_db,
    tools.summarization.list_employees_by_project_db,
    tools.summarization.list_employees_by_shift_db,
    tools.summarization.list_employees_by_hire_year_db,
]

tool_dict = {
    "fetch_employee_by_id_db": tools.summarization.fetch_employee_by_id_db,
    "list_employees_by_skill_level_db": tools.summarization.list_employees_by_skill_level_db,
    "list_employees_by_performance_rating_db": tools.summarization.list_employees_by_performance_rating_db,
    "list_employees_by_skill_db": tools.summarization.list_employees_by_skill_db,
    "list_employees_by_department_db": tools.summarization.list_employees_by_department_db,
    "list_employees_by_project_db": tools.summarization.list_employees_by_project_db,
    "list_employees_by_shift_db": tools.summarization.list_employees_by_shift_db,
    "list_employees_by_hire_year_db": tools.summarization.list_employees_by_hire_year_db,
}

logger.info(f"[Summarization Tools] {', '.join(tool_dict.keys())}")

llm_with_tools = chat_model.bind_tools(tool_list)
summarize_chain = llm.create_chain_for_task(task="summarization", llm=llm_with_tools)


def get_summarized_response(query: str):
    """
    Generates a summarized response for a given query.

    This function takes a user's query, invokes the summarization agent with tools,
    and returns a natural language summary of the information retrieved from the
    database or other tools.

    Args:
        query (str): The user's query for summarization.

    Returns:
        str: The summarized response.
    """
    session = Session(db.engine)

    logger.info("Generating summary")

    response = llm_with_tools.invoke(query)

    logger.info(f"Response: {response}")

    response_content = response.content

    if response.tool_calls == []:
        return response_content

    tool_calls = response.tool_calls

    # TODO: Set flag for single and chained tool call
    try:
        tool_response = ""
        for tool_call in tool_calls:
            name, args, _tool_id = tool_call["name"], tool_call["args"], tool_call["id"]
            func = tool_dict.get(name, None)

            if func == None:
                raise Exception(f"Function not found")

            logger.info(f"Tool: {name} | Args: {args} | ID: {_tool_id}")

            args["session"] = session

            response = func.invoke(args)

            logger.info(f"Tool Response: {response}")
            response_string = dumps(response)
            tool_response += f"{name}: {response_string}"

        response = summarize_chain.invoke(
            {"query": query, "tool_response": tool_response}
        )
        summarized_response = response.content
        logger.info(f"Summarized Response: {summarized_response}")
        return summarized_response
    except Exception as e:
        logger.info(f"Summarization failed due to: {e}")
        return response_content
