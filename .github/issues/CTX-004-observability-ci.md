# [CTX-004] Hardened Containerization, Prometheus Metrics & Automated CI

> **Ticket ID**: CTX-004  
> **Phase**: Week 4 Capstone (Extended Deadline: Friday, 20 November 2026, 11:59 PM IST)  
> **Assignee**: Cohort Collaboration (@abhishekadbhute-create, @Abhinav55849, @YAKSHITH684, @mala9311)  
> **Target Components**: `Dockerfile`, `docker-compose.yml`, `.github/workflows/cortex-ci.yml`, `api/modules/telemetry_obs/`  
> **Branch**: `feature/CTX-004-<track-slug>` -> `staging`  
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

## 3. Strict Operational Engineering Schedule (Extended: Mon - Fri, Nov 20)

### Phase 1: Spec-First Infrastructure Architecture & Threat Modeling
* **Objective**: Define container specifications, threat vectors, and observability schemas.
* **Deliverables**:
  1. Author `api/modules/telemetry_obs/FEATURE_SPEC.md` and Docker security architecture specification.
  2. Map out container attack surface: root privilege escalation, file system write access, network exposure.
  3. Define Prometheus metrics taxonomy: `cortex_requests_total`, `cortex_inference_latency_seconds_bucket`, `cortex_cache_hits_total`, and `cortex_active_workers`.
  4. Submit specification for CPO architectural review.

### Phase 2: Hardened Multi-Stage Dockerfile & Docker-Compose Orchestration
* **Objective**: Construct secure, lightweight container builds.
* **Deliverables**:
  1. Author production `api/Dockerfile` using multi-stage builds. Stage 1 compiles wheels; Stage 2 installs wheels into slim runtime and enforces `USER attenomy`.
  2. Implement healthcheck instruction (`HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1`).
  3. Update `docker-compose.yml` orchestrating `cortex-api` and `cortex-redis` with resource reservations (CPU limits and memory limits).

### Phase 3: Prometheus Observability & Middleware Metrics Exposition
* **Objective**: Instrument FastAPI request middleware with sub-millisecond metrics overhead.
* **Deliverables**:
  1. Implement Prometheus metrics middleware in `api/modules/telemetry_obs/service.py`.
  2. Record request duration histograms with customized latency buckets (`0.005`, `0.010`, `0.025`, `0.050`, `0.100`, `0.250`, `0.500`, `1.0`).
  3. Author verification tests in `api/modules/telemetry_obs/tests/test_telemetry.py` verifying `/metrics` and `/health` output valid status codes and counters.

### Phase 4: GitHub Actions CI Pipeline & Automated Quality Gates
* **Objective**: Build automated CI regression workflow on pull requests.
* **Deliverables**:
  1. Author `.github/workflows/cortex-ci.yml` executing on every PR targeting `main` or `staging`.
  2. Steps: checkout repository, setup Python 3.10, install dependencies, run Ruff linting, execute full Pytest regression suite across all 5 modules, and verify container build.
  3. Enforce zero tolerance for lint warnings or failed assertions.

### Phase 5: Operational Runbook, Deployment Verification & Evidence-Driven PR
* **Objective**: Complete formal infrastructure documentation and defend deployment architecture.
* **Deliverables**:
  1. Author `api/modules/telemetry_obs/RUNBOOK.md` detailing container deployment commands, Prometheus scraping configurations, and incident response playbooks.
  2. Open an Evidence-Driven Pull Request (EDPR) targeting `staging` using the mandatory Week 4 EDPR template below.
  3. Schedule live cohort code defense session with Lead / CPO Saad Md.

---

## 4. Acceptance Criteria & Quality Gates
* Multi-stage Docker container runs under non-root UID 10001 with image size < 350MB.
* Prometheus metrics endpoint (`GET /metrics`) correctly renders counters and histograms.
* GitHub Actions CI pipeline passes with 100% green status on all modules.
* Complete documentation: `FEATURE_SPEC.md` and `RUNBOOK.md`.
* 100% pass on live cohort code defense.

---

## 5. Mandatory Week 4 Evidence-Driven PR (EDPR) Template

When opening your Pull Request targeting `staging`, you must copy and complete this exact template in your PR body:

```markdown
### Attenomy Cortex Evidence-Driven Pull Request (EDPR) : Week 4 Capstone

> **Organisation**: Attenomy, Udyam-registered MSME (UDYAM-TS-02-0279596)  
> **Repository**: apps/attenomy-cortex  
> **Target Branch**: staging  
> **Ticket**: [CTX-004] Hardened Containerization, Prometheus Metrics & Automated CI  

---

#### 1. Scope & Architectural Justification (ADR)
* **Author**: <GitHub Username>
* **Assigned Component**: <Docker Hardening / Prometheus Telemetry / Automated CI>
* **Relates to Issue**: #4
* **Design Approach**: <Brief 2-3 sentence technical justification of choices made (e.g. multi-stage slim image vs alpine, custom middleware vs third-party exporters).>
* **Alternatives Evaluated & Rejected**: <e.g. Rejected single-stage alpine due to PyTorch/ONNX wheel compilation overhead.>

---

#### 2. Infrastructure & Security Proof
* **Non-Root Verification**: Container executes strictly as `USER attenomy` (UID 10001, GID 10001).
* **Final Docker Image Size**: `<XXX> MB` (Must be strictly under 350MB).
* **Vulnerability Scan**: Zero High or Critical CVEs reported via `docker scout` / `trivy`.
* **Healthcheck**: `HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1` verified.

---

#### 3. Prometheus Observability & Automated Test Evidence
Paste terminal output showing all tests passing:

```text
pytest -v
# PASTE RAW TERMINAL OUTPUT HERE
```

* **Total Tests Passed**: <e.g. 168 passed>
* **Metrics Render Proof**: Paste raw sample output of `GET /metrics` showing `cortex_requests_total` and `cortex_inference_latency_seconds_bucket`.

---

#### 4. Video Demo Walkthrough
* **60-90 Second Loom Video**: `<https://loom.com/...>`  
  *(Must demonstrate single-command boot `docker compose up -d`, live `curl /health`, and Prometheus `/metrics` scraping).*

---

#### 5. 2-Minute Code Defense Readiness
- [ ] I have 100% line-by-line comprehension of all committed code and am ready to defend it live.
- [ ] No hardcoded secrets, internal tokens, or sensitive API keys are committed.
- [ ] All failure states return explicit HTTP 4xx JSON errors rather than unhandled 500 crashes.
- [ ] Container runs exclusively as non-root user `attenomy`.
- [ ] Zero em dashes or en dashes exist anywhere in code, comments, or documentation.
```
