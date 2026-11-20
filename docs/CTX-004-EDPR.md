# Attenomy Cortex Evidence-Driven Pull Request (EDPR): CTX-004

> Target branch: `staging`
> Assigned component: Automated CI
> Change: use Python 3.11 in CI and the Docker image, and install patched `filelock` and Pillow versions.

## 1. Scope and architectural decision

The failing security scan showed that the Python 3.10 environment resolved vulnerable `filelock 4.1.0` and `pillow 12.3.0`. Their fixed releases require Python 3.11 or newer, so both CI and the Docker base image now target Python 3.11. `api/requirements.txt` constrains `filelock>=4.2.1` and `Pillow>=13.0.0`, so both CI and Docker resolve fixed releases. CI also enforces `setuptools>=84.1.0` before dependency installation.

## 2. Infrastructure and security proof

- Docker build and image size were not verified locally.
- The provided failed CI audit identified 17 filelock and 42 Pillow findings in vulnerable installed versions. Verify the new resolved package versions and `pip-audit` result in the next GitHub Actions run.
- A local `pip-audit` run found 6 findings in developer-environment-only `datasets 3.6.0` and `setuptools 78.1.0`. It no longer reported filelock or Pillow findings. PyTorch CPU wheels were skipped because their local version suffixes are not on PyPI.

## 3. Pytest execution evidence

Command:

```text
.venv\\Scripts\\python.exe -m pytest --basetemp=.pytest-tmp-ctx004-r3 -o cache_dir=.pytest-cache-ctx004-r3 --cov=api/modules --cov-report=term-missing -rs
```

Result: **138 passed, 30 skipped in 106.54s**. The skips are model-dependent intent-router tests; the required ONNX model artifact is absent. Full terminal output, including test names, coverage, and skip reasons, is in [CTX-004-pytest.log](CTX-004-pytest.log).

This run used Windows, Python 3.12.4, pytest 9.2.0, and pytest-cov 7.1.0. It verifies the test suite locally; Python 3.11 dependency installation and the security scan still require confirmation in GitHub Actions.

## 4. Video walkthrough

No video URL was present in the repository or provided with this change. Add the actual 60-90 second Loom, YouTube, or Drive URL here before submitting the EDPR; no URL has been invented.

## 5. Code defense readiness

- [ ] Contributor has reviewed the Python 3.11 target and dependency constraints.
- [ ] Secrets review completed.
- [ ] CI Python 3.11 install and security scan are green.
- [ ] Video walkthrough URL added.
