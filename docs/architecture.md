# AI Kubernetes SRE Agent — Architecture

## M1: Local Kubernetes Incident Environment

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
6. EndpointSlices
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
ClusterIP:10.96.133.111
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

## Security Boundary

The future SRE agent uses the `sre-agent` ServiceAccount.

It is bound to the `sre-readonly` Role.

The agent can inspect Kubernetes resources but cannot modify them.

### Allowed operations

* Get, list, and watch Pods
* Get, list, and watch Deployments
* Get, list, and watch ReplicaSets
* Get, list, and watch Services
* Get, list, and watch Events
* Get, list, and watch Endpoints
* Get Pod logs

### Disallowed operations

The agent is not granted permissions for:

* Create
* Update
* Patch
* Delete

This means the agent cannot directly modify the Kubernetes environment.

## Design Principle

> **The agent should have eyes, but no hands.**

It can collect evidence, analyze the situation, and recommend remediation, but Kubernetes RBAC prevents it from changing the environment.

## Future AI Architecture

M1 deliberately keeps the AI layer separate from the Kubernetes environment.

M2 will introduce the AI investigation layer:

```text
                         AI SRE Agent
                              │
                              ▼
                         Tool Layer
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

The AI will not receive arbitrary shell access or unrestricted `kubectl` access.

Instead, it will interact with explicitly defined tools such as:

```text
get_pods()
describe_pod()
get_pod_logs()
get_events()
get_deployment()
get_services()
get_endpoints()
```

This allows the agent's capabilities to be explicitly defined and constrained.

## M1 Outcome

M1 establishes a reproducible Kubernetes incident environment with:

* A healthy PostgreSQL dependency
* A checkout service
* A deterministic failure scenario
* CrashLoopBackOff behavior
* Observable logs and Kubernetes events
* A reproducible investigation path
* Read-only Kubernetes RBAC
* A clear security boundary for future AI tooling

M1 provides the operational foundation for building the AI-powered SRE investigation agent in M2.
