#!/bin/sh

python3 -m venv /venv
source /venv/bin/activate
pip install --upgrade pip
pip install poetry
poetry install
echo "installed pip packages"