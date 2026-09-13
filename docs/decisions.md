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

The future SRE agent uses a dedicated `sre-agent` ServiceAccount with a namespace-scoped read-only Role.

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

Instead, the agent will receive explicit, narrowly scoped tools such as:

```text
get_pods()
describe_pod()
get_pod_logs()
get_events()
get_deployment()
get_services()
get_endpoints()
```

This makes the agent's capabilities explicit, auditable, and easier to secure.

---

## ADR-007: Separate Evidence Collection from AI Reasoning

### Decision

The Kubernetes tool layer will collect evidence, while the AI layer will interpret that evidence.

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

M1 and the initial AI implementation will use a single SRE investigation agent.

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

M1 uses local Kubernetes. GKE, Cloud Logging, and Cloud Monitoring will be introduced in later milestones.

### Why

Separating local incident simulation from cloud observability keeps the initial project small and inexpensive.

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

## Security Principle

The core security principle of this project is:

> **The AI should have eyes, but no hands.**

The agent should be capable of understanding what is happening inside the Kubernetes environment while being technically prevented from changing it without an explicit human-controlled approval mechanism.
