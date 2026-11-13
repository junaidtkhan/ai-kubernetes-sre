from types import SimpleNamespace
import json

from agent.mcp_adapter import (
    mcp_tools_to_openai,
    mcp_result_to_text,
)


def test_mcp_tools_to_openai_converts_tool_schema():
    mcp_tool = SimpleNamespace(
        name="get_pods",
        description="List pods in a namespace",
        input_schema={
            "type": "object",
            "properties": {
                "namespace": {"type": "string"}
            },
            "required": ["namespace"],
        },
    )

    result = mcp_tools_to_openai([mcp_tool])

    assert result == [
        {
            "type": "function",
            "function": {
                "name": "get_pods",
                "description": "List pods in a namespace",
                "parameters": mcp_tool.input_schema,
            },
        }
    ]


def test_mcp_tools_to_openai_handles_missing_description():
    mcp_tool = SimpleNamespace(
        name="get_events",
        description=None,
        input_schema={"type": "object"},
    )

    result = mcp_tools_to_openai([mcp_tool])

    assert result[0]["function"]["description"] == ""


def test_mcp_result_to_text_returns_structured_content_as_json():
    result = SimpleNamespace(
        is_error=False,
        structured_content={"result": [{"name": "checkout"}]},
        content=[],
    )

    converted = mcp_result_to_text(result)

    assert json.loads(converted) == {
        "result": [{"name": "checkout"}]
    }


def test_mcp_result_to_text_joins_text_blocks():
    result = SimpleNamespace(
        is_error=False,
        structured_content=None,
        content=[
            SimpleNamespace(text="First log line"),
            SimpleNamespace(text="Second log line"),
        ],
    )

    converted = mcp_result_to_text(result)

    assert converted == "First log line\nSecond log line"


def test_mcp_result_to_text_prioritizes_errors():
    result = SimpleNamespace(
        is_error=True,
        structured_content={"result": "should not be returned"},
        content=[
            SimpleNamespace(text="Kubernetes API unavailable"),
        ],
    )

    converted = json.loads(mcp_result_to_text(result))

    assert converted == {
        "error": True,
        "details": ["Kubernetes API unavailable"],
    }


def test_mcp_result_to_text_handles_empty_result():
    result = SimpleNamespace(
        is_error=False,
        structured_content=None,
        content=[],
    )

    converted = json.loads(mcp_result_to_text(result))

    assert converted == {
        "error": "MCP tool returned no usable content."
    }
