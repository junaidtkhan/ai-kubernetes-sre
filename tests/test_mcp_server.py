import pytest
from mcp import Client
from agent import tools as k8s_tools
from agent.mcp_server import server
from types import SimpleNamespace
import json



@pytest.mark.anyio
async def test_mcp_tool_discovery():
    async with Client(server) as client:
        result = await client.list_tools()

    tool_names = {tool.name for tool in result.tools}

    expected_tools = {
        "get_pods",
        "get_pod_logs",
        "describe_pod",
        "get_events",
        "get_deployment",
        "get_services",
        "get_endpoints",
    }

    assert tool_names == expected_tools




@pytest.mark.anyio
async def test_get_pods_rejects_invalid_namespace():
    async with Client(server) as client:
        for namespace in ["", "INVALID", "demo/prod"]:
            result = await client.call_tool(
                "get_pods",
                {"namespace": namespace},
            )

            assert result.is_error




@pytest.mark.anyio
async def test_describe_pod_rejects_invalid_pod_name():
    async with Client(server) as client:
        invalid_names = [
            "",
            "INVALID",
            "checkout/service",
            "checkout..service",
        ]

        for pod_name in invalid_names:
            result = await client.call_tool(
                "describe_pod",
                {
                    "namespace": "demo",
                    "pod_name": pod_name,
                },
            )

            assert result.is_error





@pytest.mark.anyio
async def test_get_pod_logs_rejects_invalid_tail_lines():
    async with Client(server) as client:
        for tail_lines in [0, 1001, -1, "200", True]:
            result = await client.call_tool(
                "get_pod_logs",
                {
                    "namespace": "demo",
                    "pod_name": "checkout-service",
                    "tail_lines": tail_lines,
                },
            )

            assert result.is_error




@pytest.mark.anyio
async def test_get_pod_logs_rejects_invalid_previous_type():
    async with Client(server) as client:
        for previous in ["false", "true", 0, 1, None]:
            result = await client.call_tool(
                "get_pod_logs",
                {
                    "namespace": "demo",
                    "pod_name": "checkout-service",
                    "previous": previous,
                },
            )

            assert result.is_error




@pytest.mark.anyio
async def test_get_pods_calls_existing_tool(monkeypatch):
    expected = [{"name": "checkout-service-test"}]

    def mock_get_pods(namespace):
        assert namespace == "demo"
        return expected

    monkeypatch.setattr(k8s_tools, "get_pods", mock_get_pods)

    async with Client(server) as client:
        result = await client.call_tool(
            "get_pods",
            {"namespace": "demo"},
        )

    assert not result.is_error


    response = json.loads(result.content[0].text)

    assert response["items"] == expected
    assert response["total"] == 1
    assert response["returned"] == 1
    assert response["truncated"] is False





@pytest.mark.anyio
async def test_get_pods_propagates_tool_error(monkeypatch):
    def mock_get_pods(namespace):
        raise RuntimeError("Kubernetes API unavailable")

    monkeypatch.setattr(k8s_tools, "get_pods", mock_get_pods)

    async with Client(server) as client:
        result = await client.call_tool(
            "get_pods",
            {"namespace": "demo"},
        )

    assert result.is_error





@pytest.mark.anyio
async def test_get_deployment_preserves_secret_redaction(monkeypatch):
    expected = {
        "name": "checkout-service",
        "env": {
            "DATABASE_URL": "postgresql://postgres:***@postgres:5432/orders",
            "API_TOKEN": "***",
        },
    }

    def mock_get_deployment(namespace, deployment_name):
        return expected

    monkeypatch.setattr(
        k8s_tools,
        "get_deployment",
        mock_get_deployment,
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "get_deployment",
            {
                "namespace": "demo",
                "deployment_name": "checkout-service",
            },
        )

    assert not result.is_error
    assert "***" in str(result)
    assert "password123" not in str(result)
    assert "secret-token" not in str(result)




@pytest.mark.anyio
async def test_get_pod_logs_calls_existing_tool(monkeypatch):
    expected = "Application started successfully"

    def mock_get_pod_logs(
        namespace,
        pod_name,
        tail_lines=200,
        previous=False,
    ):
        assert namespace == "demo"
        assert pod_name == "checkout-service"
        assert tail_lines == 50
        assert previous is True
        return expected

    monkeypatch.setattr(
        k8s_tools,
        "get_pod_logs",
        mock_get_pod_logs,
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "get_pod_logs",
            {
                "namespace": "demo",
                "pod_name": "checkout-service",
                "tail_lines": 50,
                "previous": True,
            },
        )

    assert not result.is_error
    assert expected in str(result)




@pytest.mark.anyio
async def test_get_pod_logs_truncates_large_output(monkeypatch):
    from agent.mcp_server import MAX_LOG_CHARS

    expected = "A" * (MAX_LOG_CHARS + 5000)

    monkeypatch.setattr(
        k8s_tools,
        "get_pod_logs",
        lambda *args, **kwargs: expected,
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "get_pod_logs",
            {
                "namespace": "demo",
                "pod_name": "checkout-service",
            },
        )

    assert not result.is_error

    response = result.content[0].text

    assert response.startswith("A" * MAX_LOG_CHARS)
    assert len(response[:MAX_LOG_CHARS]) == MAX_LOG_CHARS
    assert "[TRUNCATED:" in response
    assert len(response) < len(expected)




@pytest.mark.anyio
async def test_get_pods_truncates_large_output(monkeypatch):
    expected = [{"name": f"pod-{i}"} for i in range(150)]

    monkeypatch.setattr(
        k8s_tools,
        "get_pods",
        lambda namespace: expected,
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "get_pods",
            {"namespace": "demo"},
        )

    assert not result.is_error

    response = json.loads(result.content[0].text)

    assert len(response["items"]) == 100
    assert response["total"] == 150
    assert response["returned"] == 100
    assert response["truncated"] is True




def test_get_deployment_redacts_sensitive_values(monkeypatch):
    deployment = SimpleNamespace(
        metadata=SimpleNamespace(
            name="checkout-service",
            namespace="demo",
        ),
        spec=SimpleNamespace(
            replicas=1,
            template=SimpleNamespace(
                spec=SimpleNamespace(
                    containers=[
                        SimpleNamespace(
                            name="checkout",
                            image="checkout:latest",
                            ports=[],
                            env=[
                                SimpleNamespace(
                                    name="DATABASE_URL",
                                    value="postgresql://postgres:password123@postgres:5432/orders",
                                ),
                                SimpleNamespace(
                                    name="API_TOKEN",
                                    value="secret-token",
                                ),
                                SimpleNamespace(
                                    name="APP_MODE",
                                    value="production",
                                ),
                            ],
                        )
                    ]
                )
            ),
        ),
        status=SimpleNamespace(
            ready_replicas=1,
            available_replicas=1,
        ),
    )

    monkeypatch.setattr(
        k8s_tools.k8s.apps,
        "read_namespaced_deployment",
        lambda name, namespace: deployment,
    )

    result = k8s_tools.get_deployment("demo", "checkout-service")

    env = {
        item["name"]: item["value"]
        for item in result["containers"][0]["env"]
    }

    assert env["DATABASE_URL"] == (
        "postgresql://postgres:***@postgres:5432/orders"
    )
    assert env["API_TOKEN"] == "***"
    assert env["APP_MODE"] == "production"
    assert "password123" not in str(result)
    assert "secret-token" not in str(result)



@pytest.mark.anyio
async def test_describe_pod_truncates_events(monkeypatch):
    expected_events = [
        {"reason": f"Event-{i}"}
        for i in range(75)
    ]

    monkeypatch.setattr(
        k8s_tools,
        "describe_pod",
        lambda namespace, pod_name: {
            "name": pod_name,
            "events": expected_events,
        },
    )

    async with Client(server) as client:
        result = await client.call_tool(
            "describe_pod",
            {
                "namespace": "demo",
                "pod_name": "checkout-service",
            },
        )

    assert not result.is_error

    response = json.loads(result.content[0].text)

    assert len(response["events"]["items"]) == 50
    assert response["events"]["total"] == 75
    assert response["events"]["returned"] == 50
    assert response["events"]["truncated"] is True