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
    Render a clear, structured text description of a list of tools for LLM consumption.
    """
    descriptions = []
    for tool in tools:
        desc_lines = []
        # Tool name
        desc_lines.append(f"Tool Name: {tool.name}")

        # Signature
        if hasattr(tool, "func") and tool.func:
            sig = signature(tool.func)
            desc_lines.append(f"Signature: {sig}")

        # Description and Args
        tool_description = tool.description or (
            tool.func.__doc__ if hasattr(tool, "func") and tool.func else ""
        )
        if tool_description:
            # Extract Args section if present
            args_match = re.search(
                r"Args:\s*(.*?)\n(?:Returns:|Raises:|$)", tool_description, re.DOTALL
            )
            if args_match:
                args_text = args_match.group(1).strip()
                # Format args as bullet points
                args_lines = [
                    f"  - {line.strip()}" for line in args_text.split("\n") if line.strip()
                ]
                desc_lines.append("Arguments:")
                desc_lines.extend(args_lines)
                # Add description before Args if any
                desc_before_args = tool_description.split("Args:")[0].strip()
                if desc_before_args:
                    desc_lines.insert(2, f"Description: {desc_before_args}")
            else:
                # No Args section, just add full description
                desc_lines.append(f"Description: {tool_description.strip()}")
        else:
            desc_lines.append("Description: No description available.")

        descriptions.append("\n".join(desc_lines))

    # Join all tool descriptions with clear separators
    return "\n\n" + ("-" * 40) + "\n\n".join(descriptions) + "\n"