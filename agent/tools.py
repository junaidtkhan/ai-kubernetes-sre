import re
from .kubernetes_client import KubernetesClient


k8s = KubernetesClient()


def get_pods(namespace: str) -> list[dict]:
    pods = k8s.core.list_namespaced_pod(namespace=namespace)

    results = []

    for pod in pods.items:
        restart_count = sum(
            container.restart_count or 0
            for container in (pod.status.container_statuses or [])
        )

        ready = all(
            container.ready
            for container in (pod.status.container_statuses or [])
        )

        results.append(
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "ready": ready,
                "restarts": restart_count,
                "node": pod.spec.node_name,
            }
        )

    return results

def get_pod_logs(
    namespace: str,
    pod_name: str,
    tail_lines: int = 200,
    previous: bool = False,
) -> str:
    logs = k8s.core.read_namespaced_pod_log(
        name=pod_name,
        namespace=namespace,
        tail_lines=tail_lines,
        previous=previous,
    )

    if isinstance(logs, bytes):
        return logs.decode("utf-8")

    if isinstance(logs, str) and logs.startswith("b'") and logs.endswith("'"):
        return logs[2:-1].encode("utf-8").decode("unicode_escape")

    return logs

def describe_pod(namespace: str, pod_name: str) -> dict:
    pod = k8s.core.read_namespaced_pod(
        name=pod_name,
        namespace=namespace,
    )

    containers = []

    for container in pod.status.container_statuses or []:
        state = container.state

        current_state = {
            "running": state.running is not None,
            "waiting": state.waiting is not None,
            "terminated": state.terminated is not None,
        }

        terminated = None

        if state.terminated:
            terminated = {
                "reason": state.terminated.reason,
                "exit_code": state.terminated.exit_code,
            }

        containers.append(
            {
                "name": container.name,
                "ready": container.ready,
                "restart_count": container.restart_count,
                "state": current_state,
                "terminated": terminated,
            }
        )

    events = k8s.core.list_namespaced_event(
        namespace=namespace,
        field_selector=f"involvedObject.name={pod_name}",
    )

    event_results = [
        {
            "type": event.type,
            "reason": event.reason,
            "message": event.message,
        }
        for event in events.items
    ]

    return {
        "name": pod.metadata.name,
        "namespace": pod.metadata.namespace,
        "status": pod.status.phase,
        "pod_ip": pod.status.pod_ip,
        "node": pod.spec.node_name,
        "containers": containers,
        "events": event_results,
    }

def get_events(namespace: str) -> list[dict]:
    events = k8s.core.list_namespaced_event(
        namespace=namespace,
    )

    return [
        {
            "type": event.type,
            "reason": event.reason,
            "message": event.message,
        }
        for event in events.items
    ]

def get_deployment(namespace: str, deployment_name: str) -> dict:
    deployment = k8s.apps.read_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
    )

    containers = []

    for container in deployment.spec.template.spec.containers:
        env = []

        for variable in container.env or []:
            value = variable.value

            if value and any(
                keyword in variable.name.lower()
                for keyword in ["password", "secret", "token", "key"]
            ):
                value = "***"

            elif value and variable.name == "DATABASE_URL":
                value = re.sub(
                    r"(://[^:]+:)[^@]+(@)",
                    r"\1***\2",
                    value,
                )

            env.append(
                {
                    "name": variable.name,
                    "value": value,
                }
            )

        containers.append(
            {
                "name": container.name,
                "image": container.image,
                "ports": [
                    port.container_port
                    for port in (container.ports or [])
                ],
                "env": env,
            }
        )

    return {
        "name": deployment.metadata.name,
        "namespace": deployment.metadata.namespace,
        "replicas": deployment.spec.replicas,
        "ready_replicas": deployment.status.ready_replicas or 0,
        "available_replicas": deployment.status.available_replicas or 0,
        "containers": containers,
    }

def get_services(namespace: str) -> list[dict]:
    services = k8s.core.list_namespaced_service(
        namespace=namespace,
    )

    return [
        {
            "name": service.metadata.name,
            "namespace": service.metadata.namespace,
            "type": service.spec.type,
            "cluster_ip": service.spec.cluster_ip,
            "ports": [
                {
                    "port": port.port,
                    "target_port": port.target_port,
                    "protocol": port.protocol,
                }
                for port in (service.spec.ports or [])
            ],
            "selector": service.spec.selector or {},
        }
        for service in services.items
    ]

def get_endpoints(namespace: str) -> list[dict]:
    endpoints = k8s.core.list_namespaced_endpoints(
        namespace=namespace,
    )

    results = []

    for endpoint in endpoints.items:
        addresses = []

        for subset in endpoint.subsets or []:
            for address in subset.addresses or []:
                addresses.append(
                    {
                        "ip": address.ip,
                        "pod": (
                            address.target_ref.name
                            if address.target_ref
                            else None
                        ),
                    }
                )

        ports = []

        for subset in endpoint.subsets or []:
            for port in subset.ports or []:
                ports.append(
                    {
                        "port": port.port,
                        "protocol": port.protocol,
                    }
                )

        results.append(
            {
                "name": endpoint.metadata.name,
                "namespace": endpoint.metadata.namespace,
                "addresses": addresses,
                "ports": ports,
            }
        )

    return results