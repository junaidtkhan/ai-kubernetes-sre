from kubernetes import client, config


class KubernetesClient:
    def __init__(self):
        try:
            config.load_incluster_config()
            print("Loaded in-cluster Kubernetes configuration.")
        except config.ConfigException:
            config.load_kube_config()
            print("Loaded local kubeconfig.")

        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()