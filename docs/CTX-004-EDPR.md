# Attenomy Cortex Evidence-Driven Pull Request (EDPR): CTX-004

> **Organisation**: Attenomy, Udyam-registered MSME (UDYAM-TS-02-0279596)
> **Repository**: apps/attenomy-cortex
> **Target Branch**: staging
> **Ticket**: [CTX-004] Hardened Containerization, Prometheus Metrics & Automated CI

---

## 1. Scope and Architectural Justification (ADR)

* **Author**: Abhinav55849 (Abhinav Singh)
* **Assigned Component**: Automated CI
* **Feature Branch**: feature/CTX-004-ci-pipeline
* **Relates to Issue**: #4 (CTX-004)
* **Design Approach**: GitHub Actions workflow with two separate jobs. The lint job installs only ruff 0.17.4. The test job installs CPU torch, the project requirements, runs pip-audit 2.10.1, then runs pytest with coverage. Permissions are read only, concurrency cancels older runs on the same branch, and pip caching is keyed on the requirements files. CI and the Docker base image use Python 3.11, because the pip-audit fix versions (filelock 4.2.1 and Pillow 13.0.0) require Python 3.11 or newer. `api/requirements.txt` sets `filelock>=4.2.1` and `Pillow>=13.0.0`, and the CI install step sets `setuptools>=84.1.0`.
* **Alternatives Evaluated and Rejected**:
  - Keep Python 3.10 and ignore the Pillow findings with `--ignore-vuln`: rejected, because there are 42 Pillow advisory IDs and Pillow is used in OCR and image code.
  - Pin `filelock<=4.1.0` on Python 3.10: rejected, because CI run 44747378034 reported 17 filelock findings for 4.1.0 and the pinned version cannot clear them.
  - Keep Python 3.10 and only document the audit blocker: rejected, because fixed versions are available on Python 3.11.
* **Deviation from ticket**: the ticket specifies Python 3.10 for CI and `python:3.10-slim` for the image. This PR uses Python 3.11. Approval from Saad Md. is requested in the PR comments.

---

## 2. Infrastructure and Security Proof

* **pip-audit history**: the first CI run (44747378034) failed with 59 findings: 17 in filelock 4.1.0 and 42 in Pillow 12.3.0. After the Python 3.11 change and the version constraints, the GitHub checks `Pytest and Security Scan (pull_request)` (successful in 1m) and `Ruff Lint (pull_request)` (successful in 7s) are green.
* **Resolved versions from the CI log (Python 3.11.18)**: filelock 4.2.4, setuptools 84.2.1, torch 2.15.0+cpu, torchvision 0.29.2+cpu. Pillow version: not shown in the log excerpt. The pip-audit step reports "No known vulnerabilities found".
* **Known pip-audit limit**: torch and torchvision `+cpu` wheels cannot be audited by pip-audit because they are not on PyPI. The CI log shows both skipped for this reason. This is documented in `docs/CI_RUNBOOK.md`.
* **Local pip-audit (developer venv)**: 6 findings remain in `datasets 3.6.0` and `setuptools 78.1.0`. Neither is in the project requirements, and CI does a fresh install, so they do not appear in CI. filelock and Pillow are no longer reported locally.
* **Non-root user, final image size, container CVE scan, healthcheck**: N/A for the Automated CI track. These belong to the Docker track (teammate).
* **docker-build job (ticket Phase 4, "verify container build")**: deferred. It is not added because the Dockerfile is owned by a teammate and was not verified to build. Docker is not installed on my workstation, so the `python:3.11-slim` change in `api/Dockerfile` is unverified locally.
* **Latency profiling**: N/A for the CI track.

---

## 3. Automated Test Execution Evidence

Command (local, Windows, Python 3.12.4, pytest 9.2.0, pytest-cov 7.1.0):

```text
.venv\Scripts\python.exe -m pytest --basetemp=.pytest-tmp-ctx004-r3 -o cache_dir=.pytest-cache-ctx004-r3 --cov=api/modules --cov-report=term-missing -rs
```

* **Local result**: 168 collected, **138 passed, 30 skipped, 0 failed** in 106.54s.
* **CI result** (Ubuntu, Python 3.11.18, `pytest --cov=api/modules --cov-report=term-missing -rs`): 168 collected, **138 passed, 30 skipped, 0 failed** in 9.06s.
* **Skips**: all 30 are intent router tests. The files `model.onnx`, `tokenizer.json`, `labels.json` and `calibration.json` are not committed to git. No test is skipped because of a missing system package or Redis. The same 30 tests are skipped in CI.
* **Full raw output** (test names, coverage, skip reasons): [CTX-004-pytest.log](CTX-004-pytest.log).
* **Lint**: `ruff check api/` reports "All checks passed!".

---

## 4. Video Demo Walkthrough

* **Video Link**: https://drive.google.com/file/d/1-CyErMA6hpNW4rhujLEKZWRQEA-j1xbU/view?usp=sharing

---

## 5. 2-Minute Code Defense Readiness

- [ ] I have line-by-line comprehension of all committed code and am ready to defend it live.
- [ ] No hardcoded secrets, internal tokens, or sensitive API keys are committed.
- [ ] All failure states return explicit HTTP 4xx JSON errors rather than unhandled 500 crashes (not changed by this PR).
- [ ] Container runs exclusively as non-root user `attenomy` (N/A for the CI track).
- [ ] Zero em dashes or en dashes exist anywhere in code, comments, or documentation.

---

## 6. Preferred Review Slot

Sunday, 22 November 2026, 7:00 PM IST.