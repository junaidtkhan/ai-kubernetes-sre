import sys
import os

from kubernetes import client, config


class KubernetesClient:
    def __init__(self):
        auth_mode = os.getenv("K8S_AUTH_MODE", "local")

        if auth_mode == "incluster":
            config.load_incluster_config()
            print("Loaded in-cluster Kubernetes configuration.", file=sys.stderr)

        elif auth_mode == "local":
            config.load_kube_config()
            print("Loaded local Kubernetes configuration.", file=sys.stderr)

        else:
            raise ValueError(
                f"Unsupported K8S_AUTH_MODE: {auth_mode}"
            )

        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()
