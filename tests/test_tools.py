from agent.tools import (
    get_pods,
    get_pod_logs,
    describe_pod,
    get_events,
    get_deployment,
    get_services,
    get_endpoints,
)


NAMESPACE = "demo"


def test_get_pods():
    result = get_pods(NAMESPACE)
    assert isinstance(result, list)


def test_get_pod_logs():
    pods = get_pods(NAMESPACE)
    pod_name = pods[0]["name"]

    result = get_pod_logs(NAMESPACE, pod_name)

    assert isinstance(result, str)


def test_describe_pod():
    pods = get_pods(NAMESPACE)
    pod_name = pods[0]["name"]

    result = describe_pod(NAMESPACE, pod_name)

    assert isinstance(result, dict)
    assert result["name"] == pod_name


def test_get_events():
    result = get_events(NAMESPACE)
    assert isinstance(result, list)


def test_get_deployment():
    result = get_deployment(NAMESPACE, "checkout-service")

    assert isinstance(result, dict)
    assert result["name"] == "checkout-service"


def test_get_services():
    result = get_services(NAMESPACE)

    assert isinstance(result, list)


def test_get_endpoints():
    result = get_endpoints(NAMESPACE)

    assert isinstance(result, list)