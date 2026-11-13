import json



def mcp_tools_to_openai(mcp_tools: list) -> list[dict]:
    """Convert MCP tool definitions into OpenAI function schemas."""

    openai_tools = []

    for tool in mcp_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        })

    return openai_tools





def mcp_result_to_text(result) -> str:
    """Convert an MCP tool result into JSON text for the LLM."""

    text_blocks = [
        item.text
        for item in result.content
        if hasattr(item, "text")
    ]

    if result.is_error:
        return json.dumps({
            "error": True,
            "details": text_blocks,
        })

    if result.structured_content is not None:
        return json.dumps(result.structured_content)

    if text_blocks:
        return "\n".join(text_blocks)

    return json.dumps({
        "error": "MCP tool returned no usable content."
    })