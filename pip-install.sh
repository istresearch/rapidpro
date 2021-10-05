#!/bin/sh

python3 -m venv venv
source venv/bin/activate
pip install setuptools==33.1.1
pip install --exists-action=w -r pip-freeze.txt
pip install --exists-action=w -r pip-add-reqs.txt
echo "installed pip packages"
