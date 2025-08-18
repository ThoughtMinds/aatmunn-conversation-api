from langchain_core.tools.base import BaseTool
from inspect import signature
import re


def render_text_description(tools: list[BaseTool]) -> str:
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
