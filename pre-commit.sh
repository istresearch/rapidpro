#!/bin/sh

# auto check for pep8 so we don't check in bad code
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -e '\.py$')

if [ -n "$FILES" ]; then
    black --line-length=119 --quiet $FILES 
fi

if [ -n "$FILES" ]; then
    flake8 $FILES 
fi
