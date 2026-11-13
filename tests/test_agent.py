import json
from types import SimpleNamespace

import pytest

from agent import agent


class FakeMCP:
    def __init__(self):
        self.called_tools = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def list_tools(self):
        tool = SimpleNamespace(
            name="get_pods",
            description="List pods",
            input_schema={
                "type": "object",
                "properties": {
                    "namespace": {"type": "string"}
                },
            },
        )
        return SimpleNamespace(tools=[tool])

    async def call_tool(self, name, arguments):
        self.called_tools.append((name, arguments))

        return SimpleNamespace(
            is_error=False,
            structured_content={
                "result": [{"name": "checkout-service"}]
            },
            content=[],
        )


class FakeOpenAI:
    def __init__(self):
        self.responses = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=None,
                            tool_calls=[
                                SimpleNamespace(
                                    id="call_123",
                                    function=SimpleNamespace(
                                        name="get_pods",
                                        arguments='{"namespace": "demo"}',
                                    ),
                                )
                            ],
                            model_dump=lambda exclude_none=True: {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [],
                            },
                        )
                    )
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Checkout pod investigation complete.",
                            tool_calls=None,
                        )
                    )
                ]
            ),
        ]

        self.requests = []

    def chat_completions_create(self, **kwargs):
        self.requests.append(kwargs)
        return self.responses.pop(0)


class FakeChat:
    def __init__(self, openai_client):
        self.completions = SimpleNamespace(
            create=openai_client.chat_completions_create
        )


@pytest.mark.anyio
async def test_agent_discovers_and_executes_mcp_tool(monkeypatch):
    fake_mcp = FakeMCP()
    fake_openai = FakeOpenAI()
    fake_openai.chat = FakeChat(fake_openai)

    monkeypatch.setattr(
        agent,
        "Client",
        lambda params: fake_mcp,
    )
    monkeypatch.setattr(
        agent,
        "get_openai_client",
        lambda: fake_openai,
    )

    result = await agent.ask_ai("Investigate checkout-service.")

    assert result == "Checkout pod investigation complete."

    assert fake_mcp.called_tools == [
        ("get_pods", {"namespace": "demo"})
    ]

    assert len(fake_openai.requests) == 2

    second_request_messages = fake_openai.requests[1]["messages"]

    tool_messages = [
        message
        for message in second_request_messages
        if message["role"] == "tool"
    ]

    assert len(tool_messages) == 1
    assert tool_messages[0]["tool_call_id"] == "call_123"

    tool_result = json.loads(tool_messages[0]["content"])

    assert tool_result == {
        "result": [{"name": "checkout-service"}]
    }



@pytest.mark.anyio
async def test_agent_rejects_tool_not_discovered_from_mcp(monkeypatch):
    fake_mcp = FakeMCP()
    fake_openai = FakeOpenAI()
    fake_openai.chat = FakeChat(fake_openai)

    fake_openai.responses = [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=None,
                        tool_calls=[
                            SimpleNamespace(
                                id="call_unauthorized",
                                function=SimpleNamespace(
                                    name="delete_pod",
                                    arguments='{"namespace": "demo"}',
                                ),
                            )
                        ],
                        model_dump=lambda exclude_none=True: {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [],
                        },
                    )
                )
            ]
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="The requested tool was not authorized.",
                        tool_calls=None,
                    )
                )
            ]
        ),
    ]

    monkeypatch.setattr(
        agent,
        "Client",
        lambda params: fake_mcp,
    )
    monkeypatch.setattr(
        agent,
        "get_openai_client",
        lambda: fake_openai,
    )

    result = await agent.ask_ai("Delete the checkout pod.")

    assert result == "The requested tool was not authorized."

    # No MCP tool was executed.
    assert fake_mcp.called_tools == []

    # The agent returned an error to the model.
    tool_messages = [
        message
        for message in fake_openai.requests[1]["messages"]
        if message["role"] == "tool"
    ]

    assert len(tool_messages) == 1

    error = json.loads(tool_messages[0]["content"])

    assert error["error"] is True
    assert "Tool not allowed: delete_pod" in error["details"]




@pytest.mark.anyio
async def test_agent_stops_after_max_iterations(monkeypatch):
    fake_mcp = FakeMCP()
    fake_openai = FakeOpenAI()
    fake_openai.chat = FakeChat(fake_openai)

    repeated_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[
                        SimpleNamespace(
                            id="call_repeat",
                            function=SimpleNamespace(
                                name="get_pods",
                                arguments='{"namespace": "demo"}',
                            ),
                        )
                    ],
                    model_dump=lambda exclude_none=True: {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [],
                    },
                )
            )
        ]
    )

    fake_openai.responses = [
        repeated_response
        for _ in range(agent.max_iterations)
    ]

    monkeypatch.setattr(
        agent,
        "Client",
        lambda params: fake_mcp,
    )
    monkeypatch.setattr(
        agent,
        "get_openai_client",
        lambda: fake_openai,
    )

    with pytest.raises(
        RuntimeError,
        match="exceeded the maximum",
    ):
        await agent.ask_ai("Investigate repeatedly.")

    assert len(fake_openai.requests) == agent.max_iterations
    assert len(fake_mcp.called_tools) == agent.max_iterations