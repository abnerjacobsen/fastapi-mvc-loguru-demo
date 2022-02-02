#!/usr/bin/env bash

if [ -n "$DEBUG" ]; then
	set -x
fi

set -o errexit
set -o nounset
set -o pipefail

POETRY_HOME="${POETRY_HOME:=${HOME}/.poetry}"
"$POETRY_HOME"/bin/poetry run flake8 --select=E,W,I --max-line-length 80 --import-order-style pep8 --exclude .git,__pycache__,.eggs,*.egg,.pytest_cache,mvc_demo/version.py,mvc_demo/__init__.py --tee --output-file=pep8_violations.txt --statistics --count mvc_demo
"$POETRY_HOME"/bin/poetry run flake8 --select=D --ignore D301 --tee --output-file=pep257_violations.txt --statistics --count mvc_demo
"$POETRY_HOME"/bin/poetry run flake8 --select=C901 --tee --output-file=code_complexity.txt --count mvc_demo
"$POETRY_HOME"/bin/poetry run flake8 --select=T --tee --output-file=todo_occurence.txt --statistics --count mvc_demo tests
"$POETRY_HOME"/bin/poetry run black -l 80 --check mvc_demo
