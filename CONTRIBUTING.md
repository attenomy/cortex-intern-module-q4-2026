# Attenomy Cortex Contributor Guidelines

Welcome to the **Attenomy Cortex** engineering repository. This document defines the engineering standards, branching conventions, and pull request verification protocols for all contributors, including software engineering and machine learning interns.

Attenomy operates with production-grade engineering rigor. We follow an **Evidence-Driven Engineering Protocol** where claims are verified by automated test suites, profiling benchmarks, and live code defenses.

---

## 1. Branching & Git Workflow

We enforce a strict branching protocol to protect staging and production environments:

* **Protected Branches**: Direct commits or pushes to `main` or `staging` are strictly forbidden.
* **Feature Branches**: All work must originate from an updated `staging` branch:
  ```bash
  git checkout staging
  git pull origin staging
  git checkout -b feature/CTX-001-neural-intent-router
  ```
* **Branch Naming Standard**: `feature/<ticket-id>-<slug>` (e.g. `feature/CTX-002-document-classifier`, `fix/CTX-001-timeout-bug`).
* **Semantic Commit Messages**: Every commit must follow semantic conventions:
  - `feat(router): add pre-warmed ONNX runtime model initialization`
  - `test(router): add negative tests for empty and long queries`
  - `fix(extract): catch unhandled base64 decoding errors with HTTP 422`
  - `docs(api): document sub-50ms latency benchmark parameters`

---

## 2. Evidence-Driven Pull Request (EDPR) Standard

Before opening a pull request, contributors must compile concrete technical evidence. Pull requests lacking evidence will be immediately rejected without senior code review.

Every pull request must fulfill the 5 pillars of the EDPR:

1. **Architectural Decisions (ADR)**: Justify why you chose your specific architecture or model, and state what alternative was rejected.
2. **Automated Test Output**: Paste unfiltered terminal output proving all unit and edge-case tests pass.
3. **Edge-Case Test Ratio**: At least 60% of test cases must test negative inputs, boundary conditions, and error recovery.
4. **Latency Profiling Proof**: Run local load testing to verify p95 latency remains strictly under 50.0ms on CPU.
5. **Video Walkthrough Link**: A 60-90 second walkthrough video demonstrating your feature working in real time.

---

## 3. The 2-Minute Live Code Defense

Before any pull request is merged into `staging`:

* The contributor must be prepared to defend their pull request in a live 2-minute walkthrough during standup or 1-on-1 review.
* Tech leads probe error handling, edge cases, model memory footprint, and concurrency safety.
* Unchecked AI-generated boilerplate that the contributor cannot explain will result in immediate rejection.

---

## 4. Development & Testing Setup

1. **Clone & Environment Setup**:
   ```bash
   cd apps/attenomy-cortex/api
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   pip install -r requirements.txt
   pip install pytest pytest-cov httpx
   ```

2. **Running the API Locally**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. **Running the Test Suite**:
   ```bash
   pytest tests/ -v --cov=services --cov=main
   ```

4. **Formatting & Quality Gates**:
   - Line-wrapping in documentation must not truncate.
   - Strictly avoid em dashes or en dashes anywhere in text, commit messages, or code comments. Use standard hyphens, colons, or parentheses instead.

