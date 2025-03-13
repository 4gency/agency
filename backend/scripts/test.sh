#!/usr/bin/env bash

set -e
set -x

pytest app/tests --cov=app --cov-report=term-missing -n auto
coverage report --show-missing
coverage html --title "${@-coverage}"
