# Runbook: Automated CI Pipeline (CTX-004)

> Repository: apps/attenomy-cortex  
> Component: `.github/workflows/cortex-ci.yml`  
> Track: CI/CD Quality Gates & Automated Regression Testing  
> Supervisor: Saad Md. (saad@attenomy.com), Founder & CPO  

---

## 1. Executive Summary & Pipeline Objective

The Attenomy Cortex continuous integration (CI) pipeline automates code quality, vulnerability scanning, and regression testing for every change targeting `staging` or `main`.

Its primary objectives are:
- Enforce strict code formatting and linting standards via pinned Ruff 0.17.4.
- Prevent regressions across query routing, cognitive document extraction, semantic caching, document ingestion, and telemetry modules.
- Ensure dependency security by auditing installed packages against known CVEs using pip-audit 2.10.1.
- Accelerate build turnaround via pip caching and lightweight CPU-only PyTorch wheels.

---

## 2. Pipeline Triggers & Concurrency

### Triggers
The workflow executes on:
- **Pushes** to `main` and `staging`.
- **Pull Requests** targeting `main` and `staging`.

```yaml
on:
  push:
    branches: [ main, staging ]
  pull_request:
    branches: [ main, staging ]
```

### Security Permissions
Least-privilege permissions are enforced at the top level:
```yaml
permissions:
  contents: read
```
This blocks write access to repository contents, releases, packages, and issues.

### Concurrency Group
```yaml
concurrency:
  group: cortex-ci-${{ github.ref }}
  cancel-in-progress: true
```
Subsequent pushes to an active pull request immediately cancel redundant in-flight builds.

---

## 3. Jobs and Execution Details

The workflow is divided into two focused jobs:

### Job 1: `lint` (Ruff Lint)
- **Runner**: `ubuntu-latest`
- **Timeout**: 10 minutes
- **Environment**: Python 3.10
- **Tool**: Pinned `ruff==0.17.4`
- **Command**: `ruff check api/`
- **Objective**: Verifies compliance with import order, syntax, and coding standards defined in `pyproject.toml`.

### Job 2: `test` (Pytest and Security Scan)
- **Runner**: `ubuntu-latest`
- **Timeout**: 30 minutes
- **Environment**: Python 3.10 with pip caching keyed on:
  - `api/requirements.txt`
  - `api/modules/semantic_cache/requirements.txt`
- **Step 1: Install Dependencies**:
  - Upgrades `pip`, `setuptools`, and `wheel`.
  - Installs lightweight CPU-only PyTorch and torchvision wheels via `--index-url https://download.pytorch.org/whl/cpu` to avoid downloading multi-gigabyte CUDA binaries.
  - Installs dependencies from `api/requirements.txt`.
  - Upgrades `fsspec` to resolve known transitive vulnerabilities.
  - Installs `pytest`, `pytest-cov`, `httpx`, and pinned `pip-audit==2.10.1`.
- **Step 2: Security Scan with pip-audit**:
  - Scans all installed packages against the OSV and PyPI vulnerability databases.
- **Step 3: Run Pytest Test Suite**:
  - Executes `pytest --cov=api/modules --cov-report=term-missing -rs`.

---

## 4. How to Run the Same Checks Locally

Always run and verify these checks on your machine before pushing commits:

```powershell
# 1. Activate your virtual environment
.venv\Scripts\activate

# 2. Run Ruff linting
.venv\Scripts\python -m ruff check api/

# 3. Run the full test suite with module coverage and skip reporting
.venv\Scripts\python -m pytest --cov=api/modules -q -rs

# 4. Run pip-audit security scan
.venv\Scripts\pip-audit.exe
```

---

## 5. How to Read and Triage a Red Run

When a CI run fails, click the red cross on GitHub Actions and inspect the failing job:

### A. Failure in `lint` (Ruff)
- **Indicator**: Step `Lint Code with Ruff` exits with code 1, listing file names and error codes (e.g. `I001` unsorted imports, `F401` unused import).
- **Remediation**: Run `.venv\Scripts\python -m ruff check api/ --fix` locally, review diffs, commit, and push.

### B. Failure in `test` (pip-audit)
- **Indicator**: Step `Security Scan with pip-audit` reports a table of package names, vulnerability IDs, and fix versions.
- **Remediation**: See Section 7 on handling pip-audit findings below.

### C. Failure in `test` (Pytest)
- **Indicator**: Step `Run Pytest Test Suite` prints failing test names with assertion tracebacks.
- **Remediation**: Run the specific test locally:
  ```powershell
  .venv\Scripts\python -m pytest api/modules/<module>/tests/<test_file>.py -v
  ```
  Investigate logic regressions, mock mismatches, or schema deviations.

---

## 6. How to Refresh the Pip Cache

GitHub Actions caches pip downloads based on hash keys of:
- `api/requirements.txt`
- `api/modules/semantic_cache/requirements.txt`

If a cached wheel is corrupted or dependencies drift without file modification:
1. **Automated Refresh via File Update**: Adding or modifying a pin in `api/requirements.txt` changes the cache key, triggering a fresh download.
2. **Manual Cache Deletion via GitHub UI**:
   - Go to repository **Actions** -> **Caches** (in the left management sidebar).
   - Locate the cache prefixed with `cortex-ci-` or `Linux-pip-`.
   - Click the trash icon to delete the cache entry.
   - The next workflow run will rebuild the pip cache from scratch.

---

## 7. How to Handle a pip-audit Finding

When `pip-audit` detects a CVE in an installed package:
1. Review the output table containing package name, current version, advisory ID, and fix version.
2. Check whether the package is a direct dependency in `api/requirements.txt` or a sub-module requirements file.
3. **Primary Remediation (Upgrade)**:
   - If direct, update the version constraint in `api/requirements.txt` to or above the fix version.
   - If transitive, upgrade it explicitly in `api/requirements.txt` or via a dedicated upgrade step in CI (similar to `pip install --upgrade fsspec "filelock>=4.2.1"`).
4. **Secondary Remediation (Documented Exception)**:
   - If an upstream fix is unavailable and the vulnerability is non-exploitable in Cortex runtime context, use `--ignore-vuln <VULN_ID>`.
   - Every `--ignore-vuln` flag must be accompanied by a documented exception comment in the workflow detailing the advisory ID, reason for exemption, date, and supervisor sign-off.
   - Never quietly ignore vulnerabilities or add packages like `datasets` (which is not part of production requirements) to ignore lists.
5. Run `.venv\Scripts\pip-audit.exe` locally to confirm the advisory is cleared and zero conflicts exist.

---

## 8. Known Limitations & Edge Cases
### pip-audit Findings in CI Run 44747378034
- The run flagged pillow 12.3.0 and filelock 4.1.0. Both are transitive dependencies (torchvision and pytesseract bring in pillow, torch brings in filelock).
- The CI install step now upgrades them explicitly. This is not yet confirmed by a new green run: <FILL FROM REAL RUN>.
- The Docker image installs from requirements.txt and is not covered by this CI-only upgrade.
- A local virtual environment can show datasets and an old setuptools in pip-audit. CI does a fresh install, so these do not appear there.

### Intent Router Model Test Skips (30 Tests Skipped)
- The test suite reports 138 passed and 30 skipped.
- All 30 skipped tests originate from `api/tests/test_router.py` (3 tests) and `api/modules/intent_router/tests/test_intent_router.py` (27 tests).
- Skip Reason: `model.onnx`, `tokenizer.json`, `labels.json`, and `calibration.json` are not committed to git.
- Pytest decorators skip these tests when the model file is not present. This skip behavior is expected both locally and in CI.
- No tests skip due to missing system packages (such as tesseract-ocr) or services (such as Redis).

### Python Version Discrepancy (CI 3.10 vs Local 3.12)
- CI jobs execute under Python 3.10 to align with the production container base image (`python:3.10-slim`).
- Local developer environments may run Python 3.12 (e.g. Windows virtual environments).
- Both versions are supported by `pyproject.toml` (`requires-python = ">=3.10"`). When debugging environment-specific dependency issues, verify packages against Python 3.10 constraints.

### CPU PyTorch Wheels and pip-audit
- PyTorch and torchvision CPU wheels are fetched from `https://download.pytorch.org/whl/cpu` and bear local version suffixes such as `torch (2.15.0+cpu)` and `torchvision (0.29.2+cpu)`.
- Because local build tags (`+cpu`) do not match standard PyPI release names, `pip-audit` skips them with:
  `Dependency not found on PyPI and could not be audited: torch (2.15.0+cpu)`
- This is normal and expected behavior for CPU wheels; pip-audit logs the skip in its summary table without failing the build.

### Docker Build Job Status (Why Docker Job is Not Added Yet)
- Ticket CTX-004 covers Docker hardening under a teammate's track.
- `api/Dockerfile` currently has `COPY requirements.txt .` before copying `modules/`, causing `pip install -r requirements.txt` to fail during build because `-r modules/semantic_cache/requirements.txt` is not yet available in the build context.
- Furthermore, the multi-stage non-root user `USER attenomy` (UID 10001) and healthchecks have not yet landed from the container track.
- Therefore, the `docker-build` job must not be added to CI until the teammate container hardening PR is merged.
