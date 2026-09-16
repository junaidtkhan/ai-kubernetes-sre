# AI Kubernetes SRE Agent — Architecture Decisions

## ADR-001: Use a Local kind Cluster for M1

### Decision

Use [kind](https://kind.sigs.k8s.io/) to create the Kubernetes environment for M1.

### Why

The goal of M1 is to build and test the incident-investigation workflow without introducing cloud costs or unnecessary infrastructure complexity.

kind provides:

* A real Kubernetes environment
* Fast cluster creation and deletion
* Reproducible development
* No GCP infrastructure cost
* Easy local experimentation

GKE will be introduced in a later milestone.

---

## ADR-002: Use a Deterministic Failure Scenario

### Decision

Create a deliberately broken version of `checkout-service` that uses an invalid PostgreSQL hostname.

### Why

An SRE agent needs a reproducible incident that can be triggered on demand.

The healthy configuration uses:

```text
postgres:5432
```

The broken configuration uses:

```text
wrong-host:5432
```

This causes the application to fail and exit with status code `1`, producing:

```text
CrashLoopBackOff
```

A deterministic incident makes testing and demonstrations repeatable.

---

## ADR-003: Use a Kubernetes Service Instead of a Pod IP

### Decision

Applications connect to PostgreSQL through the `postgres` Kubernetes Service.

### Why

Pod IPs are ephemeral and can change when Pods are recreated.

The Service provides a stable network identity:

```text
checkout-service
       │
       ▼
postgres:5432
       │
       ▼
PostgreSQL Service
       │
       ▼
PostgreSQL Pod
```

This reflects normal Kubernetes application architecture.

---

## ADR-004: Keep the Application Simple in M1

### Decision

Use the PostgreSQL image with `pg_isready` as a lightweight diagnostic workload instead of building a complete application.

### Why

The purpose of M1 is to establish the Kubernetes incident environment, not to build a production application.

Using the existing PostgreSQL image allows us to demonstrate:

* Application startup
* Dependency connectivity
* Application failure
* Container exit codes
* Restart behavior
* CrashLoopBackOff
* Application logs

A more realistic application can be introduced later if it provides additional value.

---

## ADR-005: Use Read-Only Kubernetes RBAC

### Decision

The SRE agent uses a dedicated `sre-agent` ServiceAccount with a namespace-scoped read-only Role.

### Why

The AI should be able to investigate incidents without being able to modify the environment.

The agent can:

* Inspect Pods
* Inspect Deployments
* Inspect ReplicaSets
* Inspect Services
* Inspect Endpoints
* Inspect Events
* Read Pod logs

The agent cannot:

* Create resources
* Update resources
* Patch resources
* Delete resources

This follows the principle of least privilege.

The RBAC boundary was explicitly verified during M1:

| Operation            | Result  |
| -------------------- | ------- |
| `get pods`           | Allowed |
| `get pods/log`       | Allowed |
| `delete pods`        | Denied  |
| `create deployments` | Denied  |

---

## ADR-006: No Arbitrary kubectl or Shell Access

### Decision

The AI agent will not receive unrestricted shell access or an arbitrary `kubectl` execution tool.

### Why

A tool such as:

```text
execute_kubectl(command)
```

would effectively give the AI broad access to the Kubernetes environment.

Instead, the agent receives explicit, narrowly scoped tools such as:

```text
get_pods()
get_pod_logs()
describe_pod()
get_events()
get_deployment()
get_services()
get_endpoints()
```

This makes the agent's capabilities explicit, auditable, and easier to secure.

---

## ADR-007: Separate Evidence Collection from AI Reasoning

### Decision

The Kubernetes tool layer collects evidence, while the AI layer interprets that evidence.

### Why

The AI should not directly determine how Kubernetes API calls are implemented.

The architecture is:

```text
Kubernetes
     │
     ▼
Tool Layer
     │
     ▼
Evidence
     │
     ▼
AI Reasoning
     │
     ▼
Diagnosis
```

This separation makes the system easier to test and allows the Kubernetes tooling to be reused independently of the AI model.

The tool layer is implemented using the Kubernetes Python client rather than shelling out to `kubectl`.

---

## ADR-008: Human Approval Before Remediation

### Decision

The initial system will not automatically execute remediation actions.

### Why

Incident diagnosis and infrastructure modification have different risk levels.

The agent should initially:

1. Collect evidence
2. Identify the likely root cause
3. Explain the evidence
4. Recommend remediation
5. Wait for human approval

Only a later milestone may introduce controlled remediation with explicit approval.

This creates a clear boundary between:

```text
Observation
    ↓
Diagnosis
    ↓
Recommendation
```

and:

```text
Modification
```

---

## ADR-009: Start with a Single-Agent Architecture

### Decision

M1 and the initial AI implementation use a single SRE investigation agent.

### Why

A single agent is easier to understand, test, debug, and secure.

Multi-agent orchestration may be introduced later when there is a clear reason to separate responsibilities such as:

```text
SRE Orchestrator
       │
       ├── Kubernetes Agent
       ├── Logs Agent
       └── Metrics Agent
```

Multi-agent architecture should be added because it provides engineering value, not simply because it is possible.

---

## ADR-010: Introduce GKE and GCP Observability Later

### Decision

M1 and M2 use local Kubernetes. GKE, Cloud Logging, and Cloud Monitoring will be introduced in later milestones.

### Why

Separating local incident simulation and AI investigation from cloud infrastructure and observability keeps the initial project small and inexpensive.

The progression is:

```text
M1
Local Kubernetes
      ↓
M2
AI Investigation
      ↓
M3
MCP Tool Server
      ↓
M4
GKE + Logs + Metrics
      ↓
M5
Multi-Agent Orchestration
      ↓
M6
Human Approval + Controlled Remediation
```

This allows each architectural layer to be validated before adding additional complexity.

---

## ADR-011: Use Explicit Python Tool Functions

### Decision

Implement Kubernetes capabilities as explicit Python functions rather than exposing raw Kubernetes API access to the AI model.

### Why

The AI model should interact with a controlled interface rather than directly constructing Kubernetes API requests.

Each tool has a defined responsibility and input/output boundary:

```text
AI Agent
   │
   ├── get_pods()
   ├── get_pod_logs()
   ├── describe_pod()
   ├── get_events()
   ├── get_deployment()
   ├── get_services()
   └── get_endpoints()
```

This provides:

* Explicit capabilities
* Easier testing
* Easier auditing
* Smaller attack surface
* A clean boundary for the future MCP server

The same tool layer can later be exposed through MCP without changing the underlying Kubernetes investigation logic.

---

## ADR-012: Bound AI Investigation Iterations

### Decision

Limit the number of consecutive AI tool-call iterations during an investigation.

The current implementation allows a maximum of 10 investigation iterations.

### Why

An agentic loop should have an explicit execution boundary.

Without a limit, unexpected model behavior could cause the agent to continue requesting tools indefinitely.

The iteration limit provides:

* Predictable execution
* Protection against runaway tool calls
* Easier debugging
* Controlled API usage
* A clear failure condition

If the limit is reached, the agent stops rather than continuing indefinitely.

---

## ADR-013: Redact Sensitive Configuration Values

### Decision

Sensitive configuration values returned by Kubernetes tools must be redacted before being exposed to the AI model.

### Why

Kubernetes Deployment environment variables may contain credentials, tokens, passwords, or connection strings.

The tool layer therefore redacts values containing sensitive names such as:

```text
password
secret
token
key
```

Database connection strings are also handled specially so that credentials are not exposed:

```text
postgresql://postgres:***@wrong-host:5432/orders
```

This allows the agent to inspect configuration relevant to diagnosis while reducing unnecessary secret exposure.

---

## ADR-014: Require Evidence-Based Root-Cause Diagnosis

### Decision

The AI agent must distinguish observed evidence, contributing factors, hypotheses, and root-cause conclusions.

### Why

An incident investigation should not treat every unusual configuration value as the root cause.

The agent is instructed to build a causal evidence chain using available observations such as:

* Pod status
* Container exit state
* Application logs
* Kubernetes Events
* Deployment configuration
* Service configuration
* Endpoints

For the deterministic M2 incident, the evidence chain is:

```text
DATABASE_URL
      ↓
wrong-host:5432
      ↓
Application logs:
"wrong-host:5432 - no response"
      ↓
PostgreSQL Service:
postgres:5432
      ↓
Healthy PostgreSQL endpoint
      ↓
Database connection failure
      ↓
Container exits
      ↓
BackOff / CrashLoopBackOff
```

The agent should not label a condition as the root cause unless the available evidence establishes a causal connection.

This reduces unsupported conclusions and makes the generated incident report auditable.

---

## Security Principle

The core security principle of this project is:

> **The AI should have eyes, but no hands.**

The agent should be capable of understanding what is happening inside the Kubernetes environment while being technically prevented from changing it without an explicit human-controlled approval mechanism.
