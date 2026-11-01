# [CTX-004] Hardened Containerization, Prometheus Metrics & Automated CI

**Assignee**: Cohort Collaboration (Week 4 Capstone)  
**Target Module**: `api/modules/telemetry_obs/` & `Dockerfile` & `.github/workflows/`  
**Target Branch**: `feature/CTX-004-observability-ci` -> `staging`  
**SLA / Operational Target**: Multi-stage non-root container; Prometheus scraping format; 100% CI pass  

---

## 1. Problem Statement
The Cortex microservice requires enterprise-grade deployment isolation, continuous integration test verification on every pull request, and real-time observability into inference latency percentiles.

## 2. Deliverables & Technical Scope
1. **Multi-Stage Dockerfile**: Enforce non-root execution (`USER attenomy`, UID 10001) and slim runtime layers.
2. **Prometheus Exposition**: Build `/metrics` endpoint returning request counts and tail latency gauges.
3. **Automated CI Workflow**: GitHub Actions workflow running Ruff linting and Pytest on all PRs.
4. **Integration Verification**: Ensure `docker-compose up` orchestrates API and Redis smoothly.

## 3. Pull Request Submission
* Open PR to `staging` using `.github/PULL_REQUEST_TEMPLATE.md`.
* Include terminal pytest output and 60-90s demo video link.

