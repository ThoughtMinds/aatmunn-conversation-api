from api import db, llm, tools
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import render_text_description
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
    tools.task_execution.add_employee_db,
    tools.task_execution.update_employee_first_name_db,
    tools.task_execution.update_employee_last_name_db,
    tools.task_execution.update_employee_email_db,
    tools.task_execution.update_employee_hire_date_db,
    tools.task_execution.update_employee_department_db,
    tools.task_execution.update_employee_role_db,
    tools.task_execution.update_employee_status_db,
    tools.task_execution.delete_employee_db,
]

tool_dict = {
    "add_employee_db": tools.task_execution.add_employee_db,
    "update_employee_first_name_db": tools.task_execution.update_employee_first_name_db,
    "update_employee_last_name_db": tools.task_execution.update_employee_last_name_db,
    "update_employee_email_db": tools.task_execution.update_employee_email_db,
    "update_employee_hire_date_db": tools.task_execution.update_employee_hire_date_db,
    "update_employee_department_db": tools.task_execution.update_employee_department_db,
    "update_employee_role_db": tools.task_execution.update_employee_role_db,
    "update_employee_status_db": tools.task_execution.update_employee_status_db,
    "delete_employee_db": tools.task_execution.delete_employee_db,
}

logger.info(f"[Task Execution Tools] {', '.join(tool_dict.keys())}")

rendered_tools = render_text_description(tool_list)


llm_with_tools = chat_model.bind_tools(tool_list)

SUMMARIZE_PROMPT = """
You are an assistant that has access to the user query and corresponding API/Database response to it.
Create a summary using the available information.
Present it to the user in a short, easy to understand format. Do not add unnecessary formatting.

Query: {query}
Response: {tool_response}

Summary: 
"""

summarize_prompt = PromptTemplate.from_template(SUMMARIZE_PROMPT)

summarize_chain = summarize_prompt | chat_model


def execute_task(query: str):
    session = Session(db.engine)

    logger.info("Executing task")

    response = llm_with_tools.invoke(query)

    logger.info(f"Response: {response}")

    response_content = response.content

    if response.tool_calls == []:
        return response_content

    tool_calls = response.tool_calls

    try:
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

            response = summarize_chain.invoke(
                {"query": query, "tool_response": response_string}
            )
            summarized_response = response.content
            logger.info(f"Summarized Response: {summarized_response}")
            return summarized_response
    except Exception as e:
        logger.info(f"Task execution failed due to: {e}")
        return response_content


# TODO: Prompt user for missing details?
# TODO: Define a chained tool calling agent
