from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import StrictInt
from pydantic import StrictBool
import re

server = MCPServer("AI Kubernetes SRE")



MAX_LIST_ITEMS = 100
MAX_LOG_CHARS = 20_000


def limit_list_output(items: list, limit: int = MAX_LIST_ITEMS) -> dict:
    total = len(items)
    bounded_items = items[:limit]

    return {
        "items": bounded_items,
        "total": total,
        "returned": len(bounded_items),
        "truncated": total > limit,
    }




def validate_namespace(namespace: str) -> None:
    if (
        not isinstance(namespace, str)
        or not namespace
        or len(namespace) > 63
        or not re.fullmatch(
            r"[a-z0-9](?:[-a-z0-9]*[a-z0-9])?",
            namespace,
        )
    ):
        raise ToolError(
            "Invalid namespace: must be a valid Kubernetes "
            "namespace name (lowercase alphanumeric characters "
            "or hyphens, maximum 63 characters)."
        )

def validate_resource_name(name: str, resource_type: str) -> None:
    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= 253
        or not all(
            label
            and len(label) <= 63
            and re.fullmatch(
                r"[a-z0-9](?:[-a-z0-9]*[a-z0-9])?",
                label,
            )
            for label in name.split(".")
        )
    ):
        raise ToolError(
            f"Invalid {resource_type}: must be a valid Kubernetes "
            "resource name."
        )








@server.tool()
def get_pods(namespace: str) -> dict:
    """List pods in a Kubernetes namespace."""

    validate_namespace(namespace)

    from agent.tools import get_pods as k8s_get_pods

    return limit_list_output(k8s_get_pods(namespace))




@server.tool()
def get_pod_logs(
    namespace: str,
    pod_name: str,
    tail_lines: StrictInt = 200,
    previous: StrictBool = False,
) -> str:
    """Retrieve logs from a Kubernetes pod."""

    validate_namespace(namespace)

    validate_resource_name(pod_name, "pod name")

    if (
        isinstance(tail_lines, bool)
        or not isinstance(tail_lines, int)
        or not 1 <= tail_lines <= 1000
    ):
        raise ToolError(
            "Invalid tail_lines: must be an integer between 1 and 1000."
        )

    from agent.tools import get_pod_logs as k8s_get_pod_logs

    logs = k8s_get_pod_logs(
        namespace,
        pod_name,
        tail_lines=tail_lines,
        previous=previous,
    )

    if len(logs) > MAX_LOG_CHARS:
        logs = (
            logs[:MAX_LOG_CHARS]
            + "\n...[TRUNCATED: log output exceeded 20000 characters]"
        )

    return logs





@server.tool()
def describe_pod(namespace: str, pod_name: str) -> dict:
    """Describe a Kubernetes pod, including status and container details."""

    validate_namespace(namespace)

    validate_resource_name(pod_name, "pod name")

    from agent.tools import describe_pod as k8s_describe_pod

    result = k8s_describe_pod(namespace, pod_name)

    if isinstance(result, dict) and isinstance(result.get("events"), list):
        result["events"] = limit_list_output(
            result["events"],
            limit=50,
        )

    return result




@server.tool()
def get_events(namespace: str) -> dict:
    """Retrieve Kubernetes events from a namespace."""

    validate_namespace(namespace)

    from agent.tools import get_events as k8s_get_events

    return limit_list_output(k8s_get_events(namespace))




@server.tool()
def get_deployment(namespace: str, deployment_name: str) -> dict:
    """Retrieve details about a Kubernetes deployment."""

    validate_namespace(namespace)

    validate_resource_name(deployment_name, "deployment name")

    from agent.tools import get_deployment as k8s_get_deployment

    return k8s_get_deployment(namespace, deployment_name)




@server.tool()
def get_services(namespace: str) -> dict:
    """List Kubernetes services in a namespace."""

    validate_namespace(namespace)

    from agent.tools import get_services as k8s_get_services

    return limit_list_output(k8s_get_services(namespace))





@server.tool()
def get_endpoints(namespace: str) -> dict:
    """Retrieve Kubernetes service endpoints in a namespace."""

    validate_namespace(namespace)

    from agent.tools import get_endpoints as k8s_get_endpoints

    return limit_list_output(k8s_get_endpoints(namespace))




if __name__ == "__main__":
    server.run(transport="stdio")
