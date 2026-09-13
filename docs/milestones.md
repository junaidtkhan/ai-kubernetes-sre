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
* [x] Inspect EndpointSlices
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

**Status: Planned**

Build the first AI-powered investigation agent.

The agent should reproduce the investigation workflow performed manually in M1.

### Kubernetes Tools

Implement explicit read-only tools such as:

```text
get_pods()
describe_pod()
get_pod_logs()
get_events()
get_deployment()
get_services()
get_endpoints()
```

### Agent Workflow

The agent should:

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

### Security

* [ ] Run investigation using the `sre-agent` identity
* [ ] Prevent arbitrary shell execution
* [ ] Prevent arbitrary `kubectl` execution
* [ ] Verify tools cannot perform mutations
* [ ] Test unauthorized operations

### Output

The agent should produce reports containing:

```text
Incident
Severity
Affected Resource
Root Cause
Evidence
Recommended Remediation
Actions Taken
Confidence
```

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

### Security

The MCP layer must not provide arbitrary Kubernetes command execution.

Tools remain explicitly scoped and read-only.

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
* [ ] Compare single-agent vs multi-agent performance

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

### Testing

* [ ] Unit tests
* [ ] Kubernetes tool tests
* [ ] RBAC tests
* [ ] Incident reproduction tests
* [ ] Failure scenario tests
* [ ] Security tests

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

Create:

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
| M2        | AI SRE Investigation Agent              | Planned  |
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
