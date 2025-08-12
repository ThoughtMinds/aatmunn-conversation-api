from api import db, llm
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage
from langchain_core.tools import render_text_description
from langchain_core.messages import HumanMessage
from typing import Dict, List
from pydantic import BaseModel
from json import dumps, loads
from api.core.logging_config import logger
from sqlmodel import Session


class ToolCall(BaseModel):
    name: str
    parameters: Dict


chat_model = llm.get_ollama_chat_model()

tool_list = [
    db.add_employee_db,
    db.update_employee_first_name_db,
    db.update_employee_last_name_db,
    db.update_employee_email_db,
    db.update_employee_hire_date_db,
    db.update_employee_department_db,
    db.update_employee_role_db,
    db.update_employee_status_db,
    db.delete_employee_db
]

tool_dict = {
    "add_employee_db": db.add_employee_db,
    "update_employee_first_name_db": db.update_employee_first_name_db,
    "update_employee_last_name_db": db.update_employee_last_name_db,
    "update_employee_email_db": db.update_employee_email_db,
    "update_employee_hire_date_db": db.update_employee_hire_date_db,
    "update_employee_department_db": db.update_employee_department_db,
    "update_employee_role_db": db.update_employee_role_db,
    "update_employee_status_db": db.update_employee_status_db,
    "delete_employee_db": db.delete_employee_db
}

rendered_tools = render_text_description(tool_list)

TOOL_CALL_SYSTEM_PROMPT = f"""
You are an assistant that has access to the following set of tools. 
Here are the names and descriptions for each tool:

{rendered_tools}

Given the user input, return the name and input of the tool to use. 
Return your response as a JSON blob with 'name' and 'arguments' keys.

The `arguments` should be a dictionary, with keys corresponding 
to the argument names and the values corresponding to the requested values.
"""

# TODO: This method doesn't invoke tools, just tells you how to call the tool

tool_call_prompt = ChatPromptTemplate(
    [
        SystemMessage(
            role="system",
            content=TOOL_CALL_SYSTEM_PROMPT,
        ),
        MessagesPlaceholder("messages"),
    ]
)


llm_with_tools = chat_model.bind_tools(tool_list)

tool_call_chain = tool_call_prompt | llm_with_tools

SUMMARIZE_SYSTEM_PROMPT = f"""
You are an assistant that has access to the message history and corresponding API/Database data.
Create a response using the user query and available information. Summarize the information and present it to
the user in a short, easy to understand format. Do not add unnecessary formatting.
"""

summarize_prompt = ChatPromptTemplate(
    [
        SystemMessage(
            role="system",
            content=SUMMARIZE_SYSTEM_PROMPT,
        ),
        MessagesPlaceholder("messages"),
    ]
)

summarize_chain = summarize_prompt | chat_model


def execute_task(messages: List[HumanMessage]):
    logger.info("Executing task")
    response = tool_call_chain.invoke({"messages": messages})
    content = response.content

    session = Session(db.engine)

    try:
        # Valdiate if its a 'proper' tool call
        data = loads(content)
        tool_call = ToolCall(**data)
        logger.info(f"Found tool call: {tool_call}")

        tool_name = tool_call.name
        params = tool_call.parameters

        if tool_name and tool_name in tool_dict:
            func = tool_dict[tool_name]
            params["session"] = session

            try:
                resp = func.invoke(params)
                logger.info(f"Tool Call {tool_name} | Response: {resp}")

                json_tool_resp = dumps(resp)

                tool_message = HumanMessage(
                    content=f"Database Response: {json_tool_resp}"
                )
                messages.append(tool_message)

                logger.info(f"Messages: {messages}")

                response = summarize_chain.invoke({"messages": messages})
                summarized_response = response.content
                logger.info(f"Summarized Response: {summarized_response}")

                return summarized_response
            except Exception as e:
                logger.info(f"Failed to invoke Tool Call due to: {e}")

    except Exception as e:
        logger.info(f"Failed to convert to ToolCall due to: {e}")
        logger.info(f"Content: {content}")
        return content

# TODO: Prompt user for missing details?
# TODO: Task Content is empty, try tool call OpenAI style? (non ad-hoc)