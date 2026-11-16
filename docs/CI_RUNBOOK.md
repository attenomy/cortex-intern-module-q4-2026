# Runbook: Automated CI Pipeline (CTX-004)

> Repository: apps/attenomy-cortex  
> Component: `.github/workflows/cortex-ci.yml`  
> Track: CI/CD Quality Gates & Automated Regression Testing  
> Supervisor: Saad Md. (saad@attenomy.com), Founder & CPO  

---

## 1. Executive Summary & Purpose

The Attenomy Cortex CI pipeline provides continuous integration quality gates for every change targeting the `staging` branch. Its primary objectives are:

- Prevent regression of low-latency query routing, cognitive document extraction, semantic caching, ingestion, and telemetry modules.
- Enforce strict code formatting and linting standards via Ruff with zero warning tolerance.
- Maintain comprehensive test coverage and publish verifiable coverage artifacts on every run.
- Guard against known vulnerabilities in upstream dependencies via pip-audit with automated retry handling.
- Protect staging stability with concurrency-managed, least-privilege automated runs.

---

## 2. Pipeline Architecture & Triggers

### Triggers
- **Pull Requests**: Any pull request targeting the `staging` branch.
- **Pushes**: Any direct push to the `staging` branch (such as post-merge).

### Least-Privilege Security Permissions
The workflow declares minimal permissions at the root:
```yaml
permissions:
  contents: read
```
This blocks unauthorized token write access to repo code, releases, packages, or issues.

### Concurrency Control
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```
Pushing new commits to an open PR immediately cancels prior in-flight runs, saving runner capacity and preventing stale test reports.

### Execution Isolation & Limits
- **Runner**: `ubuntu-latest`
- **Timeout**: `timeout-minutes: 15` prevents hung jobs from consuming minutes.
- **Service Containers**: `redis:7-alpine` is provisioned on port 6379 with automated healthchecks (`redis-cli ping`).

---

## 3. Pipeline Steps in Execution Order

1. **Checkout Code**: Uses `actions/checkout@v4` to pull repository history.
2. **Set up Python 3.12**: Uses `actions/setup-python@v5` with pip caching enabled to accelerate repeat builds.
3. **Install Dependencies**:
   - Upgrades `pip` to latest.
   - Installs runtime dependencies from `api/requirements.txt` (including explicit `redis>=5.0.0,<7.0.0` and sub-module dependencies).
   - Installs testing, linting, and audit toolchains: `pytest`, `pytest-cov`, `httpx`, `ruff`, and pinned `pip-audit>=2.7`.
4. **Lint Code with Ruff**:
   - Executes `ruff check api/`.
   - Enforces rules defined in `pyproject.toml` (E, F, W, I, N, UP, B, C4).
5. **Run Pytest Test Suite with Coverage**:
   - Sets `REDIS_URL: redis://localhost:6379/0`.
   - Executes `pytest -v --cov=api --cov-report=term --cov-report=xml:coverage.xml --cov-report=html:coverage_html`.
   - Produces machine-readable XML and interactive HTML coverage reports.
6. **Upload Coverage Report Artifacts**:
   - Uses `actions/upload-artifact@v4` with `if: always()` to preserve coverage artifacts even if assertions fail.
   - Retains artifacts for 14 days.
7. **Security Audit with pip-audit**:
   - Scans all installed packages against the OSV advisory database.
   - Uses a 3-attempt retry loop with 10-second exponential pause to absorb transient network glitches.
   - Exits with a fatal non-zero code if any known unpatched CVE is identified.

---

## 4. How to Read and Triage Failures

When a CI run fails, GitHub Actions marks the job with a red cross. Click into the job details and inspect the failing step:

### A. Linting Failure (`Lint Code with Ruff`)
- **Symptom**: Step exits with code 1 and outputs file paths with rule codes (e.g. `I001`, `F401`).
- **Diagnosis**: Imports are unsorted, unused variables exist, or syntax violates formatting guidelines.
- **Remediation**: Run locally:
  ```powershell
  .venv\Scripts\python -m ruff check api/ --fix
  ```
  Review changes, commit, and push.

### B. Unit or Integration Test Failure (`Run Pytest Test Suite with Coverage`)
- **Symptom**: Pytest outputs `FAILURES` with stack traces and assertion differences.
- **Diagnosis**: A code change broke contract expectations, schema validation, or error handling.
- **Remediation**: Run the failing test file locally:
  ```powershell
  .venv\Scripts\python -m pytest api/modules/<module_name>/tests/<test_file>.py -v
  ```
  Fix the underlying logic or update mock data if contract specifications changed legitimately.

### C. Dependency or Security Audit Failure (`Security Audit with pip-audit`)
- **Symptom**: pip-audit reports known CVEs with package names and advisory IDs.
- **Diagnosis**: A pinned dependency in `api/requirements.txt` has a disclosed vulnerability.
- **Remediation**:
  1. Inspect the advisory URL printed in the CI console.
  2. Identify the patched version of the library.
  3. Update `api/requirements.txt` to the patched version.
  4. Verify locally that no dependency resolver conflicts arise.

### D. Flaky Network or Transient Step Error
- **Symptom**: Connection timeout during package installation or advisory lookup.
- **Diagnosis**: Transient GitHub runner network disconnect or PyPI rate limiting.
- **Remediation**: The pip-audit step retries up to 3 times automatically. If setup-python or pip install fails due to GitHub infrastructure outages, rerun the workflow.

---

## 5. How to Rerun the Pipeline

### Via GitHub Web UI
1. Navigate to the **Actions** tab in the repository: `https://github.com/attenomy/cortex-intern-module-q4-2026/actions`.
2. Select **Attenomy Cortex CI Pipeline** from the left sidebar.
3. Click on the failing run.
4. Click the **Re-run jobs** button in the upper right corner, then choose **Re-run all jobs** or **Re-run failed jobs**.

### Via GitHub CLI (`gh`)
```bash
gh run list --workflow=cortex-ci.yml
gh run rerun <run-id> --failed
```

### Local Reproduction Before Rerunning
Always reproduce and verify locally before triggering CI runs:
```powershell
# 1. Activate environment
.venv\Scripts\activate

# 2. Check linting
.venv\Scripts\python -m ruff check api/

# 3. Run full test suite
.venv\Scripts\python -m pytest -q

# 4. Check requirements
.venv\Scripts\python -m pip install -r api/requirements.txt
```

---

## 6. How to Add a New Check to the Pipeline

To add a new quality check (such as type checking with mypy, bandit security scanning, or docs validation):

1. **Locate Workflow File**: Open `.github/workflows/cortex-ci.yml`.
2. **Install Tooling**: If the tool requires a new package, add it to the `Install Dependencies` step.
3. **Insert Job Step**: Add the new step in the appropriate logical order. For example:
   ```yaml
   - name: Run Static Security Analysis (Bandit)
     run: |
       bandit -r api/ -x api/tests,api/modules/*/tests
   ```
4. **Local Verification**: Execute the tool locally in `.venv` and verify it exits cleanly with code 0.
5. **Document in Runbook**: Update Section 3 of this runbook to describe the purpose and remediation protocol for the new check.

---

## 7. Standards & Compliance Checklist

- [x] Workflow triggers on `pull_request` targeting `staging` and `push` to `staging`.
- [x] Least-privilege permissions (`contents: read`) enforced.
- [x] Concurrency group enabled with `cancel-in-progress: true`.
- [x] Python 3.12 with pip caching configured.
- [x] Redis service container provisioned with healthcheck.
- [x] Coverage reports generated in XML and HTML and archived as workflow artifacts.
- [x] Pinned `pip-audit>=2.7` with automated retry loop.
- [x] Zero em dashes and zero en dashes present across code, comments, and documentation.
