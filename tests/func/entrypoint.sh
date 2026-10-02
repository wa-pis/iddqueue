#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
pytest tests/unit
dramatiq-pg init
python tests/pypsql < tests/func/schema.sql
pytest tests/func
