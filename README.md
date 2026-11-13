# AI Kubernetes SRE Agent

An AI-powered Kubernetes incident investigation agent built with Python, Kubernetes, MCP, and an OpenAI-compatible LLM API.

The agent investigates Kubernetes incidents using explicitly defined, read-only tools. It collects evidence, correlates workload state with logs and Kubernetes events, identifies likely root causes, and generates structured incident reports.

**Core principle: The AI should have eyes, but not hands.**

The agent can investigate infrastructure, but it cannot modify Kubernetes resources.

## Architecture

```text
                  User
                   |
                   v
              AI SRE Agent
                   |
                   v
                MCP Client
                   |
               stdio transport
                   |
                   v
                MCP Server
                   |
                   v
           Existing Python Tools
                agent/tools.py
                   |
                   v
         Kubernetes Python Client
                   |
                   v
             Kubernetes API
                   |
                   v
             Kubernetes RBAC
                   |
                   v
          Read-only Cluster Access
```

### Components

| Component | Responsibility |
|---|---|
| AI Agent | Investigation reasoning and orchestration |
| MCP Client | Tool discovery and invocation |
| MCP Server | Input validation and tool delegation |
| Python Tools | Kubernetes API operations |
| Kubernetes RBAC | Enforces read-only permissions |
| LLM Provider | Generates hypotheses and incident reports |

## Features

- Kubernetes incident investigation.
- MCP-based tool discovery and invocation.
- Seven explicitly defined read-only Kubernetes tools.
- Pod health, restart, and readiness inspection.
- Container log and previous-container log retrieval.
- Kubernetes event inspection.
- Deployment, Service, and Endpoint analysis.
- Evidence-based root-cause reasoning.
- Sensitive configuration redaction.
- Bounded tool outputs to control model context.
- Structured incident reports.
- Restricted Kubernetes ServiceAccount.
- No automatic remediation or resource modification.

## Available MCP Tools

| Tool | Purpose |
|---|---|
| `get_pods` | Inspect pods and their status |
| `get_pod_logs` | Retrieve container logs |
| `describe_pod` | Inspect pod details and events |
| `get_events` | Inspect namespace events |
| `get_deployment` | Inspect deployment configuration |
| `get_services` | Inspect Kubernetes Services |
| `get_endpoints` | Inspect Service endpoints |

The MCP server delegates to the existing implementation in `agent/tools.py`.

The AI discovers tools dynamically through MCP rather than maintaining a separate hardcoded Kubernetes tool implementation.

## Security Model

Security is enforced at multiple layers.

1. **Explicit tool exposure:** Only registered read-only tools are available.
2. **Input validation:** Invalid namespaces, resource names, and parameters are rejected.
3. **Output controls:** Large responses are bounded and truncation is reported.
4. **Secret redaction:** Sensitive deployment environment values and database credentials are sanitized.
5. **Investigation limit:** The agent is limited to ten tool-call iterations.
6. **Kubernetes RBAC:** The ServiceAccount cannot perform destructive operations.

The agent does not expose:

```text
delete_pod()
scale_deployment()
apply_manifest()
delete_namespace()
execute_kubectl()
run_shell()
```

Kubernetes RBAC remains the final authorization boundary. Prompt instructions are not treated as a security mechanism.

## Output Limits

| Output | Limit |
|---|---:|
| Pod, event, Service, Endpoint lists | 100 records |
| Events nested in pod descriptions | 50 records |
| Log output | 20,000 characters |
| Agent investigation iterations | 10 |

List responses include `total`, `returned`, and `truncated` metadata so the agent can identify incomplete evidence.

## Incident Demonstration

The project includes a deliberately broken checkout workload.

The failure is introduced through an incorrect database hostname:

```text
postgresql://postgres:password@wrong-host:5432/orders
```

The actual Kubernetes PostgreSQL Service is named:

```text
postgres
```

The application cannot establish its database connection and repeatedly exits.

This produces a deterministic incident that the agent can investigate.

### Investigation Workflow

```text
Broken Deployment
       |
       v
CrashLoopBackOff
       |
       v
AI SRE Agent
       |
       v
MCP Tool Discovery
       |
       v
Pod Inspection
       |
       v
Logs + Events + Deployment
       |
       v
Services + Endpoints
       |
       v
Evidence Correlation
       |
       v
Root-Cause Diagnosis
       |
       v
Structured Incident Report
```

### Example Diagnosis

**Incident:** `checkout-service` failing in namespace `demo`.

**Root cause:** The application's `DATABASE_URL` references `wrong-host`, while the available PostgreSQL Service is named `postgres`.

**Evidence:**
- Checkout container logs show database connection failure.
- The configured hostname does not match the PostgreSQL Service.
- The PostgreSQL pod is healthy.
- The deployment has no ready replicas.

**Recommended remediation:** Correct the database hostname in `DATABASE_URL`.

**Action taken:** No Kubernetes resources modified. The agent only investigated and reported.

## Technology Stack

- Python
- Kubernetes
- Kubernetes Python Client
- kind
- Docker
- Model Context Protocol (MCP)
- OpenAI-compatible SDK
- OpenRouter
- pytest

## Project Structure

```text
ai-kubernetes-sre/
├── agent/
│   ├── agent.py
│   ├── kubernetes_client.py
│   ├── mcp_adapter.py
│   ├── mcp_server.py
│   ├── prompts.py
│   └── tools.py
│
├── kubernetes/
│   ├── namespace.yaml
│   ├── checkout.yaml
│   ├── broken-checkout.yaml
│   ├── postgres.yaml
│   └── rbac.yaml
│
├── tests/
│   ├── test_agent.py
│   ├── test_mcp_adapter.py
│   ├── test_mcp_server.py
│   └── test_tools.py
│
├── docs/
│   ├── architecture.md
│   ├── decisions.md
│   └── milestones.md
│
├── reports/
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11 or later.
- Docker Desktop.
- kubectl.
- kind.
- A local Kubernetes cluster.
- An OpenRouter API key.

The project has been developed and tested with Python 3.14 and a local kind cluster.

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd ai-kubernetes-sre
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create your local environment file from the example:

```bash
cp .env.example .env
```

Edit `.env` and provide your OpenRouter API key and restricted Kubernetes kubeconfig path:

```dotenv
OPENROUTER_API_KEY=your_openrouter_api_key
K8S_AUTH_MODE=local
KUBECONFIG=/Users/your-username/.kube/ai-sre-agent-config
```

The agent loads these variables automatically using `python-dotenv`.

**Security:** Never commit `.env` or share your API key. The repository ignores local environment files.

### 5. Create the local Kubernetes cluster

If you do not already have a cluster:

```bash
kind create cluster --name ai-sre
```

Configure the context:

```bash
kubectl config use-context kind-ai-sre
```

### 6. Deploy the demo environment

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/postgres.yaml
kubectl apply -f kubernetes/checkout.yaml
kubectl apply -f kubernetes/rbac.yaml
```

Wait for the workloads:

```bash
kubectl rollout status deployment/postgres -n demo
kubectl rollout status deployment/checkout-service -n demo
```

### 7. Configure restricted agent access

The agent must use the `sre-agent` ServiceAccount, which is restricted by the Kubernetes Role and RoleBinding in `kubernetes/rbac.yaml`.

Apply the RBAC manifest:

```bash
kubectl apply -f kubernetes/rbac.yaml
```

For local testing, generate a short-lived ServiceAccount token and create a dedicated kubeconfig.

**Run these commands using your administrator kubeconfig:**

```bash
AGENT_KUBECONFIG="$HOME/.kube/ai-sre-agent-config"

CLUSTER_SERVER="$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')"
CLUSTER_CA="$(kubectl config view --minify --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')"
AGENT_TOKEN="$(kubectl -n demo create token sre-agent --duration=24h)"

umask 077
mkdir -p "$HOME/.kube"

cat > "$AGENT_KUBECONFIG" <<EOF
apiVersion: v1
kind: Config
clusters:
  - name: ai-sre
    cluster:
      server: ${CLUSTER_SERVER}
      certificate-authority-data: ${CLUSTER_CA}
contexts:
  - name: ai-sre-readonly
    context:
      cluster: ai-sre
      namespace: demo
      user: sre-agent
current-context: ai-sre-readonly
users:
  - name: sre-agent
    user:
      token: ${AGENT_TOKEN}
EOF

chmod 600 "$AGENT_KUBECONFIG"
unset AGENT_TOKEN CLUSTER_CA
```

Verify the agent identity and permissions:

```bash
kubectl --kubeconfig="$AGENT_KUBECONFIG" auth whoami
kubectl --kubeconfig="$AGENT_KUBECONFIG" auth can-i get pods -n demo
kubectl --kubeconfig="$AGENT_KUBECONFIG" auth can-i delete pods -n demo
```

Expected results:

- Identity: `system:serviceaccount:demo:sre-agent`
- Reading Pods: `yes`
- Deleting Pods: `no`

Configure the agent by updating `.env`:

```dotenv
K8S_AUTH_MODE=local
KUBECONFIG=/Users/your-username/.kube/ai-sre-agent-config
```

The agent loads the restricted kubeconfig automatically.

**Important:** Never run the agent using an administrator kubeconfig. The generated token is short-lived and must be renewed when it expires.

For in-cluster deployment, change `.env` to:

```dotenv
K8S_AUTH_MODE=incluster
```

The Kubernetes client then uses the credentials mounted into the agent's Pod. `KUBECONFIG` is not required in this mode.


### 8. Run the agent

```bash
python -m agent.agent
```

The agent automatically connects to the MCP server and investigates the current incident in the `demo` namespace.

## Running Tests

Run the complete test suite:

```bash
pytest -q
```

Latest verified result:

```text
29 passed
```

The tests cover:

- AI agent behavior.
- MCP adapter conversion.
- MCP tool discovery.
- Input validation.
- Tool delegation.
- Error handling.
- Secret redaction.
- Output truncation.
- Kubernetes tool behavior.

## Project Milestones

| Milestone | Description | Status |
|---|---|---|
| M1 | Local Kubernetes incident environment | Completed |
| M2 | AI SRE investigation agent | Completed |
| M3 | MCP tool server | Completed |
| M4 | GKE and GCP observability | Planned |
| M5 | Multi-agent SRE orchestration | Planned |
| M6 | Human approval and controlled remediation | Planned |
| M7 | Documentation, demo and portfolio | In progress |

See [docs/milestones.md](docs/milestones.md) for detailed progress.

See [docs/architecture.md](docs/architecture.md) for system architecture and [docs/decisions.md](docs/decisions.md) for architecture decision records.

## Future Direction

The next planned stages include:

- Deploying the agent environment to GKE.
- Integrating Google Cloud Logging.
- Integrating Cloud Monitoring metrics and alerts.
- Introducing specialized Kubernetes, Logs, and Metrics agents.
- Building an orchestrator for cross-source incident analysis.
- Introducing human-approved remediation workflows.

Automatic production remediation is intentionally outside the current MVP.

## Design Philosophy

This project explores how AI can assist Site Reliability Engineering without receiving unrestricted infrastructure permissions.

The objective is not simply to connect an LLM to `kubectl`.

It is to build an auditable investigation workflow with explicit capabilities, least-privilege access, evidence-based reasoning, bounded execution, and human control over infrastructure changes.