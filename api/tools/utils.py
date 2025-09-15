from langchain_core.tools.base import BaseTool
from typing import List
from inspect import signature
import re


def list_tool_names(tools: List[BaseTool]):
    tool_list = []
    for tool in tools:
        name = tool.name
        normalized_name = name.replace("_", " ")
        tool_list.append(normalized_name)

    description = ""
    for index, name in enumerate(tool_list, start=1):
        description += f"{index}) {name}\n"

    return description


def render_text_description(tools: List[BaseTool]) -> str:
    """
    Render a text description of a list of tools.

    This function takes a list of BaseTool objects and generates a formatted
    string containing the names, signatures, and descriptions of the tools.

    Args:
        tools (list[BaseTool]): A list of tools to describe.

    Returns:
        str: A formatted string describing the tools.
    """
    descriptions = []
    for tool in tools:
        description = tool.name
        if hasattr(tool, "func") and tool.func:
            sig = signature(tool.func)
            description += f"{sig}"
        tool_description = tool.description or (
            tool.func.__doc__ if hasattr(tool, "func") and tool.func else ""
        )
        args_section = ""
        if tool_description:
            args_match = re.search(
                r"(.*?)(Args:.*?)(?:\n\s*(?:Returns:|Raises:|$))",
                tool_description,
                re.DOTALL,
            )
            if args_match:
                desc_before_args = args_match.group(1).strip()
                args_section = args_match.group(2).strip()
                args_section = args_section.replace("\n        ", "\n")
                description += f" - {desc_before_args}\n{args_section}"
            else:
                description += f" - {tool_description or 'No description available'}"
        descriptions.append(description)
    return "\n".join(descriptions)
