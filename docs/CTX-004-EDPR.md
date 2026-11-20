# Attenomy Cortex Evidence-Driven Pull Request (EDPR): CTX-004

> Target branch: `staging`
> Assigned component: Automated CI
> Change: use Python 3.11 in CI and the Docker image, and install patched `filelock` and Pillow versions.

## 1. Scope and architectural decision

The failing security scan showed that the Python 3.10 environment resolved vulnerable `filelock 4.1.0` and `pillow 12.3.0`. Their fixed releases require Python 3.11 or newer, so both CI and the Docker base image now target Python 3.11. `api/requirements.txt` constrains `filelock>=4.2.1` and `Pillow>=13.0.0`, so both CI and Docker resolve fixed releases. CI also enforces `setuptools>=84.1.0` before dependency installation.

## 2. Infrastructure and security proof

- Docker build and image size were not verified locally.
- The failed CI audit identified 17 filelock and 42 Pillow findings in vulnerable installed versions. The subsequent CI checks are reported successful; the status excerpt did not include resolved package versions or detailed audit output.
- A local `pip-audit` run found 6 findings in developer-environment-only `datasets 3.6.0` and `setuptools 78.1.0`. It no longer reported filelock or Pillow findings. PyTorch CPU wheels were skipped because their local version suffixes are not on PyPI.
- Reported GitHub Actions result: `Pytest and Security Scan (pull_request)` successful in 1m; `Ruff Lint (pull_request)` successful in 7s. Test count and detailed audit output were not included in the status report.

## 3. Pytest execution evidence

Command:

```text
.venv\\Scripts\\python.exe -m pytest --basetemp=.pytest-tmp-ctx004-r3 -o cache_dir=.pytest-cache-ctx004-r3 --cov=api/modules --cov-report=term-missing -rs
```

Result: **138 passed, 30 skipped in 106.54s**. The skips are model-dependent intent-router tests; the required ONNX model artifact is absent. Full terminal output, including test names, coverage, and skip reasons, is in [CTX-004-pytest.log](CTX-004-pytest.log).

This run used Windows, Python 3.12.4, pytest 9.2.0, and pytest-cov 7.1.0. It verifies the test suite locally. The Python 3.11 CI test/security and Ruff checks were subsequently reported successful.

## 4. Video walkthrough

* **Video Link**: https://drive.google.com/file/d/1-CyErMA6hpNW4rhujLEKZWRQEA-j1xbU/view?usp=sharing

## 5. Code defense readiness

- [ ] Contributor has reviewed the Python 3.11 target and dependency constraints.
- [ ] Secrets review completed.
- [x] CI Python 3.11 install and security scan are green (reported successful).
- [x] Video walkthrough URL added.

## 6. Preferred review slot

Sunday, 22 November 2026, 4:00 PM IST.
