### Attenomy Cortex Evidence-Driven Pull Request (EDPR)

> **Organisation**: Attenomy, Udyam-registered MSME (UDYAM-TS-02-0279596)  
> **Repository**: apps/attenomy-cortex  
> **Engineering Protocol**: Attenomy SOP-04 & Evidence-Driven PR Protocol  

---

#### 1. Ticket Identification & Architectural Decisions (ADR)
* **Ticket ID**: `[CTX-XXX]` (e.g. `[CTX-001]`)
* **Feature Branch**: `feature/<ticket-id>-<slug>`
* **Target Branch**: `staging`
* **Architectural Justification**: Explain why this design approach was selected.
* **Alternatives Considered & Rejected**: Document what architecture, library, or model was evaluated and rejected, and why.

---

#### 2. Automated Test Execution Evidence
Paste full, unfiltered terminal output showing all unit, integration, and edge-case tests passing:

```text
pytest tests/ -v
# PASTE RAW TERMINAL OUTPUT HERE
```

* **Total Test Cases**: 
* **Edge-Case & Negative Test Ratio**: (Minimum 60% requirement)

---

#### 3. Latency & Resource Profiling Proof
Grounded benchmarking numbers proving compliance with Attenomy Cortex's sub-50ms CPU budget:

* **Benchmarking Tool**: (Locust / cProfile / py-spy / custom script)
* **Concurrent Requests**: (e.g. 50 concurrent requests over 60 seconds)
* **Median Latency (p50)**: `XX ms`
* **Tail Latency (p95)**: `XX ms` (Must be strictly under 50.0ms on CPU)
* **Error Rate**: `0.0%`

---

#### 4. Video Demo Walkthrough
Mandatory 60-90 second technical walkthrough link demonstrating active code, curl endpoints, error states, and terminal tests:

* **Video Link**: `https://loom.com/share/...` (or YouTube / Drive link)

---

#### 5. 2-Minute Code Defense Checklist
Contributor must verify every item prior to review:

- [ ] I have line-by-line comprehension of all committed code and am prepared to defend it live.
- [ ] No hardcoded secrets, internal tokens, or sensitive API keys are committed.
- [ ] All failure modes and unparseable payloads return structured HTTP 4xx JSON errors, not unhandled 500 crashes.
- [ ] Model weights are pre-warmed during application startup (zero dynamic reloading per request).
- [ ] No em dashes or en dashes exist in documentation or code comments.

