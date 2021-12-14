#!/bin/sh

python3 -m venv /venv
source /venv/bin/activate
python3 -m pip install -U pip poetry
poetry install
echo "installed pip packages"
