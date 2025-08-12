from api import db, llm, tools
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
    tools.summarization.fetch_employee_by_id_db,
    tools.summarization.list_employees_by_skill_level_db,
    tools.summarization.list_employees_by_performance_rating_db,
    tools.summarization.list_employees_by_skill_db,
    tools.summarization.list_employees_by_department_db,
    tools.summarization.list_employees_by_project_db,
    tools.summarization.list_employees_by_shift_db,
    tools.summarization.list_employees_by_hire_year_db
]

tool_dict = {
    "fetch_employee_by_id_db": tools.summarization.fetch_employee_by_id_db,
    "list_employees_by_skill_level_db": tools.summarization.list_employees_by_skill_level_db,
    "list_employees_by_performance_rating_db": tools.summarization.list_employees_by_performance_rating_db,
    "list_employees_by_skill_db": tools.summarization.list_employees_by_skill_db,
    "list_employees_by_department_db": tools.summarization.list_employees_by_department_db,
    "list_employees_by_project_db": tools.summarization.list_employees_by_project_db,
    "list_employees_by_shift_db": tools.summarization.list_employees_by_shift_db,
    "list_employees_by_hire_year_db": tools.summarization.list_employees_by_hire_year_db
}

logger.info(f"[Summarization Tools] {', '.join(tool_dict.keys())}")

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


def get_summarized_response(messages: List[HumanMessage]):
    logger.info("Generating summary")
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
                logger.info(f"Tool Call {tool_name}")
                resp = func.invoke(params)
                logger.info(f"Tool Response: {resp}")
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