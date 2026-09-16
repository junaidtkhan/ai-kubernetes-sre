import os
import json

from openai import OpenAI

from agent.tools import get_pods, get_pod_logs, describe_pod, get_events, get_deployment, get_services, get_endpoints


client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)
max_iterations = 10

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_pods",
            "description": "Get the current status of pods in a Kubernetes namespace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace to inspect.",
                    }
                },
                "required": ["namespace"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": "Get recent logs from a Kubernetes pod.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace.",
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Name of the pod.",
                    },
                },
                "required": ["namespace", "pod_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_pod",
            "description": "Get detailed status, container states, restart information, and events for a Kubernetes pod.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace."
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Name of the pod."
                    }
                },
                "required": ["namespace", "pod_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "Get Kubernetes events from a namespace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace."
                    }
                },
                "required": ["namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_deployment",
            "description": "Get the configuration and replica status of a Kubernetes Deployment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace."
                    },
                    "deployment_name": {
                        "type": "string",
                        "description": "Name of the Deployment."
                    }
                },
                "required": ["namespace", "deployment_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_services",
            "description": "Get Kubernetes Services and their selectors, ports, and cluster IPs in a namespace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace."
                    }
                },
                "required": ["namespace"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_endpoints",
            "description": "Get Kubernetes Service endpoints and the pods currently backing those Services.",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace."
                    }
                },
                "required": ["namespace"]
            }
        }
    },
]


def ask_ai(question: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Kubernetes SRE assistant. "
                "You have read-only access to Kubernetes through explicit tools. "
                "Use the available tools to investigate before giving your conclusion. "
                "If a pod is not ready, has restarts, is failing, or is unhealthy, "
                "you must inspect its logs before concluding the investigation. "
                "Continue gathering evidence until you can provide a root-cause hypothesis. "
                "Do not stop by merely recommending another investigation step. "
                "Clearly distinguish observed evidence from assumptions. "
                "Never claim to have performed an action you did not perform. "
                "Never modify Kubernetes resources."

                "\nRoot-cause reasoning rules:\n"
                "- Treat configuration values as observations, not automatically as faults.\n"
                "- Never identify a configuration value as the root cause merely because it looks unusual or unexpected.\n"
                "- A root cause must be supported by a direct causal evidence chain.\n"
                "- Prefer evidence from application logs, container exit state, Kubernetes events, service configuration, and endpoints.\n"
                "- When multiple possible problems exist, distinguish:\n"
                "  1. Observed facts\n"
                "  2. Suspected or contributing factors\n"
                "  3. Root cause supported by evidence\n"
                "- Before declaring a root cause, ask: "
                "\"What evidence directly connects this condition to the failure?\"\n"
                "- If the evidence does not establish causality, do not present the condition as the root cause.\n"
                "- In this demo, do not treat the postgres:16 image as a root cause unless the application logs or container behavior directly demonstrate that the image is causing the failure.\n"
                "- If application logs explicitly identify a failed database connection to a specific hostname, investigate that hostname against the Kubernetes Service and endpoints before concluding.\n"

                "\nInvestigation rules:\n"
                "- Prioritize direct causal evidence from logs, events, pod state, and service configuration.\n"
                "- Do not claim that restart counts reset after recovery.\n"
                "- Do not claim service impact unless the available evidence supports it.\n"
                "- Distinguish observed evidence from inference or recommendation.\n"
                "- Do not describe an issue as DNS, networking, or application-level unless the available evidence supports that conclusion.\n"

                "\nFormat the final response as an incident report with these sections: "
                "Incident, Status, Root Cause, Evidence, Impact, Recommended Remediation, "
                "and Action Taken. "
                "Under Action Taken, explicitly state that no Kubernetes resources were modified."
            )
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    for iteration in range(max_iterations):
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            tools=tools,
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        messages.append(message)

        for tool_call in message.tool_calls:
            arguments = json.loads(tool_call.function.arguments)

            if tool_call.function.name == "get_pods":
                result = get_pods(
                    namespace=arguments["namespace"]
                )
            elif tool_call.function.name == "get_pod_logs":
                result = get_pod_logs(
                    namespace=arguments["namespace"],
                    pod_name=arguments["pod_name"],
                )
            elif tool_call.function.name == "describe_pod":
                result = describe_pod(
                    namespace=arguments["namespace"],
                    pod_name=arguments["pod_name"],
                )

            elif tool_call.function.name == "get_events":
                result = get_events(
                    namespace=arguments["namespace"],
                )

            elif tool_call.function.name == "get_deployment":
                result = get_deployment(
                    namespace=arguments["namespace"],
                    deployment_name=arguments["deployment_name"],
                )

            elif tool_call.function.name == "get_services":
                result = get_services(
                    namespace=arguments["namespace"],
                )

            elif tool_call.function.name == "get_endpoints":
                result = get_endpoints(
                    namespace=arguments["namespace"],
                )

            else:
                result = {
                    "error": f"Unknown tool: {tool_call.function.name}"
                }

            if isinstance(result, str):
                tool_result = result
            else:
                tool_result = json.dumps(result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )
    raise RuntimeError(
        f"Agent exceeded the maximum of {max_iterations} tool-call iterations."
    )


if __name__ == "__main__":
    answer = ask_ai(
        "Investigate the current incident in the demo namespace. "
        "Identify the root cause using available Kubernetes evidence. "
        "Do not stop at recommending additional investigation."
    )

    print(answer)