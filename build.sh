#!/usr/bin/env bash

set -euo pipefail

rm -rf build dist *.egg-info

python -m pip install --upgrade setuptools wheel build twine
python -m build --no-isolation
python -m twine check --strict dist/*
python -m twine upload dist/*
