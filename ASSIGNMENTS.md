# Attenomy Cortex Intern Module Assignments & PR Workflow (Weeks 3 & 4)

> **Organisation**: Attenomy, Udyam-registered MSME (UDYAM-TS-02-0279596)  
> **Repository**: apps/attenomy-cortex  
> **Engineering Protocol**: Attenomy SOP-04 & Evidence-Driven PR Protocol  
> **Lead / Signatory**: Saad Md. (`saad@attenomy.com`)  

---

## 1. Executive Summary & Modular Ownership Model
To eliminate merge conflicts, avoid cross-team blockers, and enforce true engineering ownership, **Attenomy Cortex** is partitioned into encapsulated domain modules. Each intern owns one complete operational slice: schema definitions, service logic, test suites, latency profiling, and runbooks.

---

## 2. Cohort 2026 Q4 Intern Assignments Matrix

| Assigned Intern | GitHub Handle | Assigned Module Path | Ticket ID | Target Branch | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Abhishek Adbhute** | `@abhishekadbhute-create` | `api/modules/intent_router/` | `[CTX-001]` | `feature/CTX-001-intent-router` | **ASSIGNED** |
| **Abhinav Singh** | `@Abhinav55849` | `api/modules/doc_extractor/` | `[CTX-002]` | `feature/CTX-002-doc-extractor` | **ASSIGNED** |
| **Yakshith Anandapu** | `@YAKSHITH684` | `api/modules/semantic_cache/` | `[CTX-003]` | `feature/CTX-003-semantic-cache` | **ASSIGNED** |
| **Cohort Collaboration** | All Selects | `api/modules/telemetry_obs/` | `[CTX-004]` | `feature/CTX-004-observability-ci` | **WEEK 4 CAPSTONE** |

---

## 3. End-to-End Contributor Workflow (From Assignment to Merged PR)

Every assigned intern must execute the following structured 6-step lifecycle:

```
[1. Branch from staging] -> [2. Develop in Module] -> [3. Local Pytest & Profiling]
                                                                  │
                                                                  ▼
[6. Production Merge]   <- [5. 2-Min Code Defense] <- [4. Open Evidence-Driven PR]
```

### Step 1: Branch Creation
Interns clone or pull the `attenomy-cortex` repository and checkout a fresh branch off `staging`:
```bash
git checkout staging
git pull origin staging
git checkout -b feature/<TICKET-ID>-<slug>
# Example for Abhishek:
# git checkout -b feature/CTX-001-intent-router
```

### Step 2: Isolated Module Development
Interns develop exclusively inside their assigned module directory. They do not edit other modules:
* Abhishek develops in `api/modules/intent_router/`
* Abhinav develops in `api/modules/doc_extractor/`
* Yakshith develops in `api/modules/semantic_cache/`

### Step 3: Local Verification & Latency Profiling
Before opening a PR, the intern must run their module test suite and benchmark execution speed:
```bash
# Run module unit tests
pytest modules/<module_name>/tests/ -v

# Run full API regression suite
pytest -v
```
* **Latency Requirement**: The feature must demonstrate a median latency `< 25ms` and p95 `< 50ms` on CPU.

### Step 4: Open Evidence-Driven Pull Request (EDPR)
Interns push their feature branch and open a PR against `staging` using the repository's PR template:
* Title: `feat(<module>): [CTX-XXX] <clear-actionable-summary>` (e.g. `feat(router): [CTX-001] neural intent router with sub-50ms ONNX execution (#1)`)
* Fill out all 5 EDPR sections:
  1. Architectural Decisions (ADR)
  2. Raw terminal test execution output
  3. Latency profiling proof (cProfile / Locust output)
  4. 60-90s Loom / video demonstration link
  5. Contributor Code Defense checklist

### Step 5: The 2-Minute Live Code Defense
The intern defends their pull request live with Lead / CPO Saad Md. during weekend 1-on-1 review:
* The lead probes error handling, concurrency safety, and model memory footprints.
* Unchecked AI-generated code the intern cannot explain will cause immediate rejection.

### Step 6: Merge to Staging & Production Release
Once the PR receives lead approval and passes automated GitHub Actions CI, it is merged into `staging`.

