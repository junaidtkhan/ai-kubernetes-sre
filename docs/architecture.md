# AI Kubernetes SRE Agent — Architecture

## Overview

The AI Kubernetes SRE Agent is a read-only incident investigation system for Kubernetes.

The project is designed around a simple security principle:

> **The agent should have eyes, but no hands.**

The agent can inspect Kubernetes resources, collect evidence, analyze incidents, and recommend remediation.

It cannot directly modify Kubernetes resources.

The project is built incrementally through multiple milestones, starting with a local Kubernetes incident environment and progressing toward an MCP-based, cloud-integrated SRE workflow.

---

# M1: Local Kubernetes Incident Environment

M1 provides a small, reproducible Kubernetes environment for testing AI-powered incident investigation.

## Architecture

```text
                         kind cluster

                              │

                         demo namespace

                              │

                ┌─────────────┴─────────────┐
                │                           │
          checkout-service              postgres
                │                           │
                │ DATABASE_URL              │
                └───────────┬───────────────┘
                            │
                     postgres Service
                       ClusterIP
                            │
                            ▼
                    PostgreSQL Pod
```

## Components

### checkout-service

A small diagnostic workload representing an application that depends on PostgreSQL.

Its healthy configuration connects to:

```text
postgres:5432
```

The application remains running after successfully connecting to PostgreSQL.

### PostgreSQL

A single PostgreSQL 16 pod provides the application dependency.

It is exposed through a Kubernetes ClusterIP Service named `postgres`.

Applications should use the Kubernetes Service rather than the PostgreSQL Pod IP because Pod IPs are ephemeral.

### Incident Generator

`broken-checkout.yaml` intentionally changes the database hostname:

```text
postgres:5432

      ↓

wrong-host:5432
```

The application exits with status code `1` when the connection fails.

Kubernetes restarts the container and eventually reports:

```text
CrashLoopBackOff
```

This provides a deterministic and reproducible incident for testing the SRE investigation workflow.

## Incident Investigation

The failure can be investigated using:

1. Pod status
2. Pod description
3. Container logs
4. Kubernetes events
5. Services
6. Endpoints
7. PostgreSQL health

The investigation demonstrated that:

* `checkout-service` repeatedly failed
* The container exited with code `1`
* Kubernetes reported `BackOff` events
* Application logs showed `wrong-host:5432`
* The PostgreSQL Service existed
* The PostgreSQL Service had a healthy endpoint
* PostgreSQL was accepting connections

Therefore, the root cause was an invalid database hostname in `checkout-service`.

## Kubernetes Service and Endpoint Model

The PostgreSQL Service provides a stable virtual entry point:

```text
postgres:5432

      ↓

ClusterIP

      ↓

PostgreSQL Service

      ↓

Endpoint:10.244.0.5:5432

      ↓

PostgreSQL Pod
```

The ClusterIP belongs to the Service and remains stable for the lifetime of the Service.

The endpoint IP belongs to the actual backend Pod and can change when Kubernetes replaces the Pod.

Applications therefore connect to the Service rather than directly to the Pod IP.

---

# Security Boundary

The SRE agent uses the `sre-agent` ServiceAccount.

It is bound to the `sre-readonly` Role.

The agent can inspect Kubernetes resources but cannot modify them.

## Allowed Operations

The ServiceAccount is granted read-only access to the resources required for incident investigation.

Examples include:

* Get, list, and watch Pods
* Get Pod logs
* Get, list, and watch Deployments
* Get, list, and watch ReplicaSets
* Get, list, and watch Services
* Get, list, and watch Events
* Get, list, and watch Endpoints

## Disallowed Operations

The agent is not granted permissions for:

* Create
* Update
* Patch
* Delete

The agent therefore cannot directly modify the Kubernetes environment.

This boundary is enforced by Kubernetes RBAC rather than relying only on application-level restrictions.

The verified permissions include:

```text
get pods       → yes
get pods/log   → yes
delete pods    → no
create deploy  → no
```

---

# Design Principle

> **The agent should have eyes, but no hands.**

The agent can:

* Collect evidence
* Inspect Kubernetes resources
* Analyze failures
* Identify probable root causes
* Recommend remediation
* Produce incident reports

The agent cannot:

* Delete Pods
* Create Deployments
* Modify Kubernetes resources
* Execute arbitrary shell commands
* Execute arbitrary `kubectl` commands

This provides a clear separation between investigation and remediation.

---

# M2: AI SRE Investigation Architecture

M2 introduces the AI investigation layer.

```text
                         AI SRE Agent
                              │
                              ▼
                     Explicit Tool Layer
                              │
                              ▼
                  Kubernetes Python Client
                              │
                              ▼
                       Kubernetes API
                              │
                              ▼
                       Read-only RBAC
                              │
                              ▼
                         Kubernetes
```

The AI does not receive arbitrary shell access or unrestricted `kubectl` access.

Instead, it interacts with explicitly defined read-only tools.

## Investigation Tools

The current tool layer provides:

```text
get_pods()

get_pod_logs()

describe_pod()

get_events()

get_deployment()

get_services()

get_endpoints()
```

Each tool has a specific purpose and explicit parameters.

The tools use the Kubernetes Python client to communicate with the Kubernetes API.

The AI therefore decides **what evidence it needs**, while the tool layer controls **what operations are available**.

## Tool Responsibilities

### `get_pods()`

Returns bounded information about Pods in a namespace, including:

* Pod name
* Namespace
* Phase
* Readiness
* Restart count
* Node

### `get_pod_logs()`

Retrieves bounded container logs.

Log retrieval is limited to a defined number of lines to prevent unnecessarily large responses.

The tool also supports retrieving logs from a previous container instance when available.

### `describe_pod()`

Returns diagnostic Pod information including:

* Container state
* Readiness
* Restart count
* Exit information
* Pod IP
* Node
* Related events

### `get_events()`

Retrieves Kubernetes events from the namespace to identify scheduling, startup, failure, and restart-related activity.

### `get_deployment()`

Returns deployment-level information including:

* Desired replicas
* Ready replicas
* Available replicas
* Container image
* Container ports
* Environment configuration

Sensitive environment values are redacted before being exposed to the AI.

For example:

```text
postgresql://postgres:password@wrong-host:5432/orders
```

is returned as:

```text
postgresql://postgres:***@wrong-host:5432/orders
```

### `get_services()`

Returns Kubernetes Service information including:

* Service name
* Service type
* ClusterIP
* Ports
* Selectors

### `get_endpoints()`

Returns backend endpoint information associated with Kubernetes Services.

This allows the agent to determine whether a Service has healthy backend targets.

---

# AI Investigation Flow

The investigation starts with a user request such as:

```text
Investigate why checkout-service is failing.
```

The AI can then gather evidence through the explicit tools.

```text
User
  │
  │ "Investigate checkout-service"
  ▼
AI SRE Agent
  │
  ├── get_pods()
  │
  ├── get_pod_logs()
  │
  ├── describe_pod()
  │
  ├── get_events()
  │
  ├── get_deployment()
  │
  ├── get_services()
  │
  └── get_endpoints()
          │
          ▼
   Evidence collection
          │
          ▼
   Root-cause analysis
          │
          ▼
   Incident report
```

The agent is expected to continue gathering evidence until it has enough information to establish a root-cause hypothesis.

It should not simply identify an unhealthy Pod and stop the investigation.

---

# Root-Cause Reasoning

The agent is instructed to distinguish between:

1. Observed facts
2. Suspected or contributing factors
3. Root cause supported by evidence
4. Recommended remediation

A configuration value should not automatically be considered a root cause merely because it looks unusual.

The agent should establish a direct causal evidence chain.

For the intentionally broken checkout incident, the evidence chain is:

```text
DATABASE_URL
      │
      ▼
wrong-host:5432
      │
      ▼
Application logs:
"wrong-host:5432 - no response"
      │
      ▼
PostgreSQL Service:
postgres:5432
      │
      ▼
Healthy PostgreSQL endpoint
      │
      ▼
Database connection failure
      │
      ▼
Container exits
      │
      ▼
Kubernetes BackOff / CrashLoopBackOff
```

The resulting root cause is:

```text
Invalid database hostname configured in DATABASE_URL.
```

The container image `postgres:16` may be unusual for a checkout service, but it is not identified as the root cause unless available evidence directly demonstrates that it causes the observed failure.

This distinction is important because an SRE investigation should prioritize causal evidence over assumptions.

---

# Incident Report

The AI produces a structured incident report containing:

```text
Incident
Status
Root Cause
Evidence
Impact
Recommended Remediation
Action Taken
```

The report must clearly distinguish:

* Observed evidence
* Inference
* Recommendations

The `Action Taken` section explicitly states that no Kubernetes resources were modified during the investigation.

For example:

```text
Action Taken:
No Kubernetes resources were modified.
The investigation used read-only Kubernetes tools.
```

The agent should also avoid claiming external service impact unless the available evidence establishes that impact.

For example, if a workload has zero ready replicas but there is no evidence of external traffic or a Service exposing it, the report should distinguish workload availability from confirmed user impact.

---

# Agent Safety Controls

M2 introduces several controls around the AI investigation loop.

## Explicit Tool Access

The AI can only request operations represented by defined tools.

There is no generic:

```text
execute_kubectl()
```

or:

```text
run_shell()
```

tool.

This prevents the AI from turning a natural-language request into arbitrary commands against the cluster.

## Read-Only Kubernetes Identity

The Kubernetes ServiceAccount used by the agent is restricted through RBAC.

Application-level tool restrictions therefore have a second enforcement layer at the Kubernetes API.

## Bounded Investigation Loop

The AI investigation loop has a maximum number of iterations.

This prevents an unexpected model behavior from causing an unbounded sequence of tool calls.

The current limit is:

```text
10 iterations
```

If the limit is exceeded, the agent stops instead of continuing indefinitely.

## Secret Redaction

Deployment environment values are inspected for sensitive information before being returned to the AI.

Sensitive values such as passwords, tokens, secrets, and keys are redacted.

Database connection URLs are also sanitized so credentials are not exposed.

---

# M2 Architecture

The complete M2 flow is:

```text
                         User
                           │
                           ▼
                    AI SRE Agent
                           │
                           │ Tool Calls
                           ▼
                  Explicit Tool Layer
                           │
                           ▼
                Kubernetes Python Client
                           │
                           ▼
                    Kubernetes API
                           │
                           ▼
                    Kubernetes RBAC
                           │
                    ┌──────┴──────┐
                    │             │
                  Allow         Deny
                    │             │
                    ▼             ▼
              Read-only       Mutations
              inspection      rejected
                    │
                    ▼
               Kubernetes
```

The AI therefore has visibility into the environment without having permission to change it.

---

# M1 Outcome

M1 establishes a reproducible Kubernetes incident environment with:

* A healthy PostgreSQL dependency
* A checkout service
* A deterministic failure scenario
* CrashLoopBackOff behavior
* Observable application logs
* Observable Kubernetes events
* Kubernetes Services and Endpoints
* A reproducible investigation path
* Read-only Kubernetes RBAC
* A clear security boundary for future AI tooling

M1 provides the operational foundation for building the AI-powered SRE investigation agent in M2.

---

# M2 Outcome

M2 introduces the AI-powered investigation layer with:

* Explicit Kubernetes investigation tools
* Kubernetes Python client integration
* Autonomous tool calling
* Evidence-driven investigation
* Root-cause analysis
* Structured incident reports
* Bounded investigation iterations
* Secret redaction
* Read-only Kubernetes RBAC
* No automatic remediation

The agent can investigate the intentionally broken `checkout-service` workload and identify the invalid database hostname using Kubernetes evidence.

The agent does not modify Kubernetes resources.

---

# Future Architecture

M2 intentionally keeps the AI investigation system small and focused.

Future milestones may extend the architecture with:

```text
                         AI SRE Agent
                              │
                              ▼
                         MCP Client
                              │
                              ▼
                         MCP Server
                              │
                    ┌─────────┴─────────┐
                    │                   │
               Kubernetes          Cloud APIs
                    │                   │
                    ▼                   ▼
                Kubernetes         GCP Logging
                   API             Monitoring
```

Future capabilities may include:

* MCP-based tool serving
* GKE deployment
* GCP Cloud Logging integration
* GCP Monitoring integration
* Multi-agent investigation
* Human-approved remediation

These capabilities are intentionally outside the scope of M2.
