# [CTX-004] Hardened Containerization, Prometheus Metrics & Automated CI

> **Ticket ID**: CTX-004  
> **Phase**: Week 4 Capstone (Monday - Friday / Days 16 - 20)  
> **Assignee**: Cohort Collaboration (Abhishek, Abhinav, Yakshith, Mala)  
> **Target Components**: `Dockerfile`, `docker-compose.yml`, `.github/workflows/cortex-ci.yml`, `api/modules/telemetry_obs/`  
> **Branch**: `feature/CTX-004-observability-ci` -> `staging`  
> **Supervisor / Signatory**: Saad Md. (`saad@attenomy.com`), Founder & CPO  

---

## 1. Executive Summary & Problem Context
Production deployment of Attenomy Cortex requires rigorous infrastructure security, non-root container sandboxing, deterministic CI/CD regression gates, and real-time observability. Without these enterprise guardrails:
* Containers running as root expose the host environment to container breakout vulnerabilities.
* Missing CI workflows allow regressions and broken dependencies to merge into `staging` undetected.
* Lack of structured Prometheus metrics blinds operators to production latency spikes, memory leaks, and error rates.

To achieve production release readiness, the cohort will collaborate in Week 4 to deliver an end-to-end containerized microservice running under an unprivileged user, an automated GitHub Actions CI pipeline, and real-time Prometheus metric exposition.

---

## 2. Infrastructure Standards & Security Constraints
* **Non-Root Execution**: Docker container must run as dedicated unprivileged user `USER attenomy` (UID 10001, GID 10001).
* **Multi-Stage Build Optimization**: Build stage compiles dependencies; final runtime image must use `python:3.10-slim` without compilers, temporary headers, or build tools.
* **Metrics Compliance**: Prometheus metrics exposed on `GET /metrics` must adhere strictly to Prometheus text exposition format version 0.0.4.
* **CI Quality Gate**: 100% pass rate on Ruff linting, security scans (`bandit` or `pip-audit`), and full Pytest suite across all modules.

---

## 3. Strict 5-Day Operational Engineering Schedule (Mon - Fri)

### Day 16 (Monday): Spec-First Infrastructure Architecture & Threat Modeling
* **Objective**: Define container specifications, threat vectors, and observability schemas.
* **Deliverables**:
  1. Author `api/modules/telemetry_obs/FEATURE_SPEC.md` and Docker security architecture specification.
  2. Map out container attack surface: root privilege escalation, file system write access, network exposure.
  3. Define Prometheus metrics taxonomy: `cortex_requests_total`, `cortex_inference_latency_seconds_bucket`, `cortex_cache_hits_total`, and `cortex_active_workers`.
  4. Submit specification for CPO architectural review.

### Day 17 (Tuesday): Hardened Multi-Stage Dockerfile & Docker-Compose Orchestration
* **Objective**: Construct secure, lightweight container builds.
* **Deliverables**:
  1. Author production `api/Dockerfile` using multi-stage builds. Stage 1 compiles wheels; Stage 2 installs wheels into slim runtime and enforces `USER attenomy`.
  2. Implement healthcheck instruction (`HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1`).
  3. Update `docker-compose.yml` orchestrating `cortex-api` and `cortex-redis` with resource reservations (CPU limits and memory limits).

### Day 18 (Wednesday): Prometheus Observability & Middleware Metrics Exposition
* **Objective**: Instrument FastAPI request middleware with sub-millisecond metrics overhead.
* **Deliverables**:
  1. Implement Prometheus metrics middleware in `api/modules/telemetry_obs/service.py`.
  2. Record request duration histograms with customized latency buckets (`0.005`, `0.010`, `0.025`, `0.050`, `0.100`, `0.250`, `0.500`, `1.0`).
  3. Author verification tests in `api/modules/telemetry_obs/tests/test_telemetry.py` verifying `/metrics` and `/health` output valid status codes and counters.

### Day 19 (Thursday): GitHub Actions CI Pipeline & Automated Quality Gates
* **Objective**: Build automated CI regression workflow on pull requests.
* **Deliverables**:
  1. Author `.github/workflows/cortex-ci.yml` executing on every PR targeting `main` or `staging`.
  2. Steps: checkout repository, setup Python 3.10, install dependencies, run Ruff linting, execute full Pytest regression suite across all 5 modules, and verify container build.
  3. Enforce zero tolerance for lint warnings or failed assertions.

### Day 20 (Friday): Operational Runbook, Deployment Verification & Evidence-Driven PR
* **Objective**: Complete formal infrastructure documentation and defend deployment architecture.
* **Deliverables**:
  1. Author `api/modules/telemetry_obs/RUNBOOK.md` detailing container deployment commands, Prometheus scraping configurations, and incident response playbooks.
  2. Open an Evidence-Driven Pull Request (EDPR) targeting `staging` using `.github/PULL_REQUEST_TEMPLATE.md`:
     - Section 1: Architectural Decision Record (ADR).
     - Section 2: Complete terminal output of pytest suite and GitHub Actions run green badge.
     - Section 3: Docker container scan report (`docker scout` or `trivy` showing zero high/critical CVEs).
     - Section 4: 60-90 second Loom video walkthrough demonstrating `docker-compose up` and live `/metrics` scraping.
     - Section 5: Completed 2-Minute Code Defense checklist.
  3. Schedule live cohort code defense session with Lead / CPO Saad Md.

---

## 4. Acceptance Criteria & Quality Gates
* Multi-stage Docker container runs under non-root UID 10001 with image size < 350MB.
* Prometheus metrics endpoint (`GET /metrics`) correctly renders counters and histograms.
* GitHub Actions CI pipeline passes with 100% green status on all modules.
* Complete documentation: `FEATURE_SPEC.md` and `RUNBOOK.md`.
* 100% pass on live cohort code defense.
