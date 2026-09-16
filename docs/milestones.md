# AI Kubernetes SRE Agent — Project Milestones

## Project Goal

Build a small AI-powered Kubernetes SRE / incident-response agent that can investigate infrastructure failures, collect evidence, diagnose likely root causes, and recommend remediation while maintaining strict security boundaries.

The core principle is:

> **The AI should have eyes, but no hands.**

The agent should be able to observe infrastructure without having unrestricted permission to modify it.

---

# M1 — Local Kubernetes Incident Environment

**Status: Complete**

Build a reproducible local Kubernetes environment containing a healthy application and a deliberately broken version.

### Infrastructure

* [x] Create local kind cluster
* [x] Create `demo` namespace
* [x] Deploy PostgreSQL
* [x] Create PostgreSQL ClusterIP Service
* [x] Deploy healthy `checkout-service`
* [x] Create deliberately broken `checkout-service`

### Incident Scenario

* [x] Introduce invalid PostgreSQL hostname
* [x] Produce application failure
* [x] Produce `CrashLoopBackOff`
* [x] Verify container exit code
* [x] Inspect application logs
* [x] Inspect Kubernetes events
* [x] Inspect Services
* [x] Inspect Endpoints
* [x] Verify PostgreSQL health
* [x] Identify root cause
* [x] Restore healthy application

### Security

* [x] Create dedicated `sre-agent` ServiceAccount
* [x] Create namespace-scoped read-only Role
* [x] Create RoleBinding
* [x] Verify allowed permissions
* [x] Verify denied permissions
* [x] Confirm no mutation permissions

### Documentation

* [x] Document architecture
* [x] Document architecture decisions
* [x] Document project milestones

---

# M2 — AI SRE Investigation Agent

**Status: Complete**

Build the first AI-powered investigation agent and reproduce the manual investigation workflow from M1.

### Kubernetes Tools

Implement explicit read-only tools:

```text
get_pods()
get_pod_logs()
describe_pod()
get_events()
get_deployment()
get_services()
get_endpoints()
```

* [x] Implement Kubernetes client
* [x] Implement explicit read-only tool functions
* [x] Return bounded tool output
* [x] Add Kubernetes tool tests
* [x] Verify all tools operate through the Kubernetes Python client

### Agent Workflow

The agent can:

1. Receive an incident/question
2. Inspect workload state
3. Identify suspicious workloads
4. Collect relevant evidence
5. Inspect logs
6. Inspect Kubernetes events
7. Inspect dependencies
8. Correlate evidence
9. Determine the most likely root cause
10. Produce an incident report

Implementation status:

* [x] Connect AI model to tool layer
* [x] Implement tool calling
* [x] Implement investigation loop
* [x] Add bounded investigation iterations
* [x] Add evidence-based reasoning instructions
* [x] Distinguish observed evidence from assumptions
* [x] Prevent unsupported root-cause conclusions
* [x] Produce structured incident reports

### Security

* [x] Use Kubernetes client configuration with local kubeconfig support
* [x] Support future in-cluster ServiceAccount configuration
* [x] Prevent arbitrary shell execution
* [x] Prevent arbitrary `kubectl` execution
* [x] Expose only explicit investigation tools
* [x] Keep Kubernetes operations read-only
* [x] Redact sensitive configuration values
* [x] Bound the agent investigation loop
* [x] Verify tool layer does not contain mutation operations

### Secret Protection

* [x] Redact password-like environment variables
* [x] Redact secret/token/key configuration values
* [x] Redact credentials embedded in `DATABASE_URL`
* [x] Preserve non-sensitive configuration needed for diagnosis

Example:

```text
postgresql://postgres:***@wrong-host:5432/orders
```

### Output

The agent produces reports containing:

```text
Incident
Status
Root Cause
Evidence
Impact
Recommended Remediation
Action Taken
```

The report explicitly states that Kubernetes resources were not modified.

### Testing

* [x] Kubernetes tool tests
* [x] Test Pod inspection
* [x] Test Pod log retrieval
* [x] Test Pod description
* [x] Test Events retrieval
* [x] Test Deployment inspection
* [x] Test Service inspection
* [x] Test Endpoints inspection
* [x] Run complete test suite

Current test result:

```text
7 passed
```

### M2 Incident Validation

The agent successfully investigated the deliberately broken `checkout-service` incident.

Observed evidence included:

* Checkout Pod restart activity
* Container failure state
* Application logs reporting failure to connect to `wrong-host:5432`
* PostgreSQL Service available as `postgres:5432`
* Healthy PostgreSQL endpoint
* Kubernetes BackOff events
* Invalid `DATABASE_URL` configuration

The resulting diagnosis identified the invalid database hostname as the root cause rather than treating unrelated configuration as the cause.

No Kubernetes resources were modified by the agent.

---

# M3 — MCP Tool Server

**Status: Planned**

Expose the Kubernetes investigation tools through an MCP-compatible tool server.

### Goals

* [ ] Create MCP server
* [ ] Expose Kubernetes read-only tools
* [ ] Define tool schemas
* [ ] Validate tool inputs
* [ ] Validate tool outputs
* [ ] Preserve RBAC security boundary
* [ ] Test tools independently of the AI agent
* [ ] Connect the existing investigation agent to MCP tools

### Security

The MCP layer must not provide arbitrary Kubernetes command execution.

Tools remain explicitly scoped and read-only.

The existing Python tool layer should remain the underlying implementation boundary rather than being replaced with unrestricted Kubernetes access.

---

# M4 — GKE + GCP Observability

**Status: Planned**

Move the environment from local Kubernetes to GKE and introduce cloud observability.

### GKE

* [ ] Create GKE environment
* [ ] Deploy demo workload
* [ ] Deploy incident scenario
* [ ] Configure appropriate IAM
* [ ] Configure Kubernetes RBAC
* [ ] Reproduce the incident in GKE

### Cloud Logging

Add a logs investigation capability:

```text
query_logs()
```

The agent should be able to correlate Kubernetes state with application and infrastructure logs.

### Cloud Monitoring

Add metrics investigation:

```text
query_metrics()
```

The agent should investigate signals such as:

* CPU
* Memory
* Restart rate
* Request rate
* Error rate
* Latency

### Infrastructure as Code

* [ ] Terraform configuration
* [ ] Reproducible GCP infrastructure
* [ ] Document cost controls
* [ ] Separate development/demo resources from production
* [ ] Provide cleanup instructions

---

# M5 — Multi-Agent SRE Orchestration

**Status: Planned**

Introduce specialized agents only if the additional separation provides meaningful value.

Potential architecture:

```text
                    SRE Orchestrator
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       Kubernetes       Logs Agent    Metrics Agent
          Agent
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                       Diagnosis
```

### Kubernetes Agent

Investigates:

* Pods
* Deployments
* Services
* Events
* Workload state

### Logs Agent

Investigates:

* Application logs
* Error patterns
* Log timelines
* Cloud Logging evidence

### Metrics Agent

Investigates:

* Resource utilization
* Error rates
* Latency
* Restart patterns
* Incident timing

### Orchestrator

Combines evidence from the specialized agents and produces a unified diagnosis.

* [ ] Define agent responsibilities
* [ ] Define delegation rules
* [ ] Implement orchestration
* [ ] Correlate evidence
* [ ] Compare single-agent and multi-agent approaches
* [ ] Document whether multi-agent separation provides measurable value

---

# M6 — Human Approval + Controlled Remediation

**Status: Planned**

Introduce carefully controlled remediation capabilities.

The agent must not autonomously modify infrastructure.

Potential workflow:

```text
Incident
   │
   ▼
Investigation
   │
   ▼
Diagnosis
   │
   ▼
Recommended Remediation
   │
   ▼
Human Approval
   │
   ▼
Controlled Action
   │
   ▼
Verification
```

Potential future actions could include:

```text
restart_workload()
scale_deployment()
apply_approved_change()
```

These actions must:

* Require explicit approval
* Be narrowly scoped
* Be auditable
* Validate parameters
* Record who approved the action
* Verify the result
* Fail safely

No unrestricted:

```text
kubectl exec
kubectl apply
kubectl delete
```

---

# M7 — Documentation, Demo & Portfolio

**Status: Planned**

Prepare the project for public demonstration and portfolio use.

### Documentation

* [ ] Complete README
* [ ] Architecture diagram
* [ ] Security model
* [ ] Threat model
* [ ] Tool documentation
* [ ] Deployment instructions
* [ ] Incident walkthrough
* [ ] Architecture decisions
* [ ] Milestone documentation

### Testing

* [x] Kubernetes tool tests
* [ ] RBAC tests
* [ ] Incident reproduction tests
* [ ] Failure scenario tests
* [ ] Security tests
* [ ] Integration tests
* [ ] MCP tool tests
* [ ] GKE integration tests

### Demo

Demonstrate:

```text
Healthy Kubernetes workload
        ↓
Intentional failure
        ↓
CrashLoopBackOff
        ↓
AI investigation
        ↓
Evidence collection
        ↓
Root-cause diagnosis
        ↓
Incident report
        ↓
Human-approved remediation
        ↓
Recovery verification
```

### Portfolio

* [ ] Architecture diagram
* [ ] Short demo video
* [ ] GitHub README
* [ ] Technical write-up
* [ ] LinkedIn post

---

# Milestone Progress

| Milestone | Description                             | Status   |
| --------- | --------------------------------------- | -------- |
| M1        | Local Kubernetes Incident Environment   | Complete |
| M2        | AI SRE Investigation Agent              | Complete |
| M3        | MCP Tool Server                         | Planned  |
| M4        | GKE + GCP Logs + Metrics                | Planned  |
| M5        | Multi-Agent Orchestration               | Planned  |
| M6        | Human Approval + Controlled Remediation | Planned  |
| M7        | Documentation + Demo + Portfolio        | Planned  |

---

# Architectural Progression

The project intentionally grows in stages:

```text
M1
Local Kubernetes
      │
      ▼
M2
AI Investigation
      │
      ▼
M3
MCP Tool Server
      │
      ▼
M4
GKE + Logs + Metrics
      │
      ▼
M5
Multi-Agent Orchestration
      │
      ▼
M6
Human Approval + Controlled Remediation
      │
      ▼
M7
Production-quality Documentation + Demo
```

Each milestone should provide a working system before additional complexity is introduced.

The project deliberately avoids adding future infrastructure before the current milestone has been validated.
