# Attenomy Cortex Engineering Roadmap: Weeks 3 & 4 (Product Contribution Phase)

> **Organisation**: Attenomy, Udyam-registered MSME (UDYAM-TS-02-0279596)  
> **Repository**: `attenomy/cortex-intern-module`  
> **Target Environment**: Production Release Readiness (v1.0.0)  
> **Program Phase**: Product Contribution Phase (Days 11 to 21)  
> **Author**: Saad Md. (`saad@attenomy.com`), Chief People Officer & Lead  

---

## 1. Executive Program Context

Following the completion of the trial practice phase in Weeks 1 and 2 (data cleaning, exploratory data analysis, and baseline anti-fraud pipelines in the student sandbox), engineering interns transition directly into the **Live Product Contribution Phase** on **Attenomy Cortex**.

Instead of writing toy code in an isolated folder, interns operate as production engineers on the live `attenomy/cortex-intern-module` repository. They pick up active tickets, develop in domain-scoped modules, submit Evidence-Driven Pull Requests (EDPRs), and defend their systems before executive engineering leadership.

---

## 2. Week 3 Roadmap: Deep Learning & Domain Module Engineering (Days 11 to 15)

### Phase Objective
Master deep learning mechanics from first principles, fine-tune specialized neural architectures for Attenomy Cortex, and implement pre-warmed modular service logic on dedicated ticket branches.

```
Days 11-12: NumPy MLP & Gradients -> Days 13-14: Module Implementation -> Day 15: Error Analysis & Gate 3
```

### Day-by-Day Execution Breakdown

* **Days 11 to 12 (Mon-Tue): Deep Learning Foundations & Gradient Checking**
  * Construct a 2-layer Multi-Layer Perceptron (MLP) from scratch in pure NumPy (`src/nn_from_scratch.py`). Implement forward pass, ReLU activation, Softmax output, Cross-Entropy loss, and analytical backpropagation gradients.
  * Execute two-sided finite difference numerical gradient checking, proving relative error is strictly `< 1e-5`.
  * Port architecture to PyTorch (`torch.nn.Module`, `torch.optim.AdamW`) to verify loss curve parity.
  * Benchmark MLP against Week 2's LightGBM on tabular features, testing Dropout, L2 weight decay, and early stopping.

* **Days 13 to 14 (Wed-Thu): Live Module Development on `attenomy-cortex`**
  * Interns checkout their assigned ticket branches off `staging`:
    * **Abhishek Adbhute (`[CTX-001]` / `feature/CTX-001-intent-router`)**:
      * Develops in [api/modules/intent_router/](file:///C:/Users/UwU/Desktop/@attenomy/apps/attenomy-cortex/api/modules/intent_router/).
      * Fine-tunes `DistilBERT` or `all-MiniLM-L6-v2` (or exports to ONNX runtime) to replace the keyword heuristic with semantic query routing.
      * Enforces deterministic fallback category `search` when confidence falls below `0.60`.
      * Guarantees CPU inference latency median `< 25ms` and p95 `< 50ms`.
    * **Abhinav Singh (`[CTX-002]` / `feature/CTX-002-doc-extractor`)**:
      * Develops in [api/modules/doc_extractor/](file:///C:/Users/UwU/Desktop/@attenomy/apps/attenomy-cortex/api/modules/doc_extractor/).
      * Fine-tunes a PyTorch `MobileNetV3` document layout classifier to replace the mock invoice payload.
      * Enforces schema validation confirming extracted fields contain required invoice/receipt keys (`vendor_name`, `invoice_number`, `net_amount`, `currency`).
      * Catches unparseable or corrupted payload content with clean HTTP 422 JSON errors.
    * **Yakshith Anandapu (`[CTX-003]` / `feature/CTX-003-semantic-cache`)**:
      * Develops in [api/modules/semantic_cache/](file:///C:/Users/UwU/Desktop/@attenomy/apps/attenomy-cortex/api/modules/semantic_cache/).
      * Implements Redis vector similarity cache with cosine distance matching.
      * Ensures cache hits return in `< 5ms` with `cached: true`.
      * Implements fail-open resilience: if Redis disconnects, falls back cleanly to live neural inference without raising 500 errors.

* **Day 15 (Fri): Experiment Tracking, Error Analysis Memo & Gate 3 Defense**
  * Log at least 6 distinct training runs in MLflow or Weights & Biases (varying learning rate, batch size, dropout, and backbone unfreezing schedules).
  * Author `reports/week3_dl_analysis.md` documenting the 3 most impactful improvements and 3 largest failure modes.
  * Draft 1-page Week 4 Capstone Proposal (`reports/capstone_proposal.pdf`).
  * Run local unit tests (`pytest modules/<module>/tests/ -v`).
  * **Weekend Gate 3 Defense**: Attend scheduled 1-on-1 walkthrough with Lead/CPO Saad Md. Passing Gate 3 is mandatory to unlock Week 4 productionization.

---

## 3. Week 4 Roadmap: Production Microservices, Containerization & Capstone Defense (Days 16 to 21)

### Phase Objective
Elevate machine learning models from local research checkpoints into containerized, pre-warmed production microservices running behind FastAPI, protected by comprehensive unit test suites in CI, and defended before executive leadership.

```
Days 16-18: Pre-Warmed Lifespan & CI Tests -> Days 19-20: Docker & EDPR -> Day 21: Executive Capstone Defense
```

### Day-by-Day Execution Breakdown

* **Days 16 to 18 (Mon-Wed): Pre-Warmed Lifespan Integration & Test Suite Expansion**
  * Mount model pipelines into FastAPI lifespan startup events (`@app.on_event("startup")` or async lifespan context). Models must load once into memory on startup with zero retraining or reloading per request.
  * Expand module test suites with defensive edge-case tests (minimum 60% negative test ratio targeting out-of-range payloads, empty strings, missing fields, and network timeouts).
  * Verify full local regression test suite passes with zero warnings:
    ```bash
    pytest -v --cov=modules --cov=main
    ```

* **Days 19 to 20 (Thu-Fri): Multi-Stage Dockerfile, Profiling & Evidence-Driven PR**
  * **Containerization**: Author multi-stage slim Dockerfile (`python:3.10-slim`) enforcing non-root user execution (`USER attenomy`, UID 10001), layer caching, and single-command startup.
  * **Prometheus Metrics**: Expose `GET /metrics` returning request counts and tail latency percentiles (p50, p95, p99).
  * **Latency Profiling**: Execute local load benchmark using Locust or cProfile, capturing verifiable proof that p95 latency remains strictly `< 50ms` on CPU.
  * **Video Walkthrough**: Record a 60-90 second Loom demo walking through terminal test execution, curl endpoint responses, and error-handling paths.
  * **Open Evidence-Driven PR (EDPR)**: Open PR against `staging` on GitHub (`attenomy/cortex-intern-module`) filling out all 5 sections of [.github/PULL_REQUEST_TEMPLATE.md](file:///C:/Users/UwU/Desktop/@attenomy/apps/attenomy-cortex/.github/PULL_REQUEST_TEMPLATE.md).

* **Day 21 (Fri-Sun): Executive Final Report, Capstone Presentation & Production Merge**
  * **Deliver Final Technical Report**: Publish a formal 6-10 page technical report covering executive summary, data architecture, baseline vs advanced model comparisons, ablation studies, and production latency.
  * **Deliver Model Card**: Standardized 1-page Attenomy Model Card (`reports/model_card.pdf`) defining intended domain use, training distributions, and performance metrics.
  * **15-Minute Executive Presentation**: Present slide deck (8-12 slides) to the Attenomy leadership team, including live microservice demonstration and technical failure post-mortem.
  * **2-Minute Code Defense**: Defend line-by-line mechanics, database transaction rollbacks, and concurrency locks before Lead/CPO Saad Md.
  * **Production Release**: Upon approval and passing GitHub Actions CI, the PR is merged into `staging` and promoted to `main`.

---

## 4. Summary of Deliverables by Phase

| Milestone | Target Path / Artifact | Evaluated Capability | Primary Verification SLA |
| :--- | :--- | :--- | :--- |
| **Week 3 (Mon-Tue)** | `src/nn_from_scratch.py` | NumPy backpropagation from first principles | Relative error `< 1e-5` |
| **Week 3 (Wed-Thu)** | `api/modules/<module>/` | Live feature code on `attenomy-cortex` branch | Modular test pass, p95 `< 50ms` |
| **Week 3 (Fri)** | `reports/week3_dl_analysis.md` | 6 tracked runs, error analysis & proposal | Gate 3 clearance |
| **Week 4 (Mon-Wed)** | `api/modules/<module>/tests/` | Pre-warmed model loading & defensive tests | 60%+ negative test ratio |
| **Week 4 (Thu-Fri)** | `Dockerfile` & GitHub PR | Evidence-Driven PR on `attenomy-cortex` | 5 EDPR pillars complete |
| **Week 4 (Weekend)** | `reports/final_report.pdf` & Deck | Executive presentation & 2-min Code Defense | 100% defense comprehension |
