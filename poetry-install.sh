#!/bin/sh

python3 -m venv /venv
. /venv/bin/activate
pip install --upgrade pip
pip install poetry
poetry shell
poetry install
echo "installed pip packages"
