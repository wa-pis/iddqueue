#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
pytest tests/unit
iddqueue init
python tests/pypsql < tests/func/schema.sql
pytest tests/func
