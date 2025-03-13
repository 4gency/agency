#!/usr/bin/env bash

set -e
set -x

if [ -z "$@" ]; then
    pytest app/tests -n auto --dist=loadfile
else
    pytest "$@" -n auto --dist=loadfile
fi
