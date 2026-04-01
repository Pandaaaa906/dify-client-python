# Release Checklist

## 1. Update Version

- Update `version` in `setup.py`.
- Keep `CHANGELOG.md` and `README.md` aligned with the release.

## 2. Validate Locally

```bash
python -m pip install -e . pytest pytest-cov flake8 build twine setuptools wheel
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
python -m pytest -q --cov=dify_client --cov-report=term-missing
python -m build --no-isolation
python -m twine check --strict dist/*
```

## 3. Push And Verify CI

- Push branch and wait for matrix checks (3.8/3.9/3.10/3.11/3.12) to pass.
- Merge PR only after all checks are green.

## 4. Publish

```bash
python -m twine upload dist/*
```

## 5. Post-release

- Tag release in GitHub (for example `v1.0.3`).
- Verify install in a clean environment:

```bash
python -m venv /tmp/dify-verify
/tmp/dify-verify/bin/pip install dify-client-python==1.0.3
/tmp/dify-verify/bin/python -c "import dify_client; print('ok')"
```
