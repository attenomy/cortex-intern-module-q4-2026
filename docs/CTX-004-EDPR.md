# Attenomy Cortex Evidence-Driven Pull Request (EDPR): CTX-004

> Target branch: `staging`
> Assigned component: Automated CI
> Change: constrain the CI `filelock` install to `<=4.1.0` for Python 3.10 compatibility.

## 1. Scope and architectural decision

The CI workflow now installs `filelock<=4.1.0` instead of forcing `filelock>=4.2.1`. This follows the requested compatibility correction while leaving the application dependency declarations and runtime code unchanged. The CI workflow uses Python 3.10; local verification below used Python 3.12.4, so the Python 3.10 dependency resolution still requires confirmation in GitHub Actions.

## 2. Infrastructure and security proof

- This change does not build or scan a container.
- `pip-audit` was not run as part of the local pytest verification.
- Verify the resolved `filelock` version and the `pip-audit` step in the next CI run. The repository's runbook records that an earlier CI audit flagged `filelock 4.1.0`.

## 3. Pytest execution evidence

Command:

```text
.venv\\Scripts\\python.exe -m pytest --basetemp=.pytest-tmp-ctx004 -o cache_dir=.pytest-cache-ctx004 --cov=api/modules --cov-report=term-missing -rs
```

Result: **138 passed, 30 skipped in 106.98s**. The skips are model-dependent intent-router tests; the required ONNX model artifact is absent. Full terminal output, including test names, coverage, and skip reasons, is in [CTX-004-pytest.log](CTX-004-pytest.log).

This run used Windows, Python 3.12.4, pytest 9.2.0, and pytest-cov 7.1.0. It verifies the test suite in this local environment, not the Python 3.10 install or security scan in GitHub Actions.

## 4. Video walkthrough

No video URL was present in the repository or provided with this change. Add the actual 60-90 second Loom, YouTube, or Drive URL here before submitting the EDPR; no URL has been invented.

## 5. Code defense readiness

- [ ] Contributor has reviewed the changed workflow and can explain the dependency constraint.
- [ ] Secrets review completed.
- [ ] CI Python 3.10 install and security scan are green.
- [ ] Video walkthrough URL added.
