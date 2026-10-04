"""Docs acceptance fails on malformed markup and missing local targets."""

import importlib.util
from pathlib import Path

import pytest
from docutils.utils import SystemMessage

spec = importlib.util.spec_from_file_location(
    "check_docs", Path(__file__).resolve().parents[2] / "scripts/check_docs.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def test_docs_checks(tmp_path):
    target = tmp_path / "target.md"
    target.write_text("# Target\n")
    document = tmp_path / "valid.rst"
    document.write_text("Title\n=====\n\n`Local <target.md>`_\n")
    checker.check_document(document)
    document.write_text(".. unknown-directive::\n")
    with pytest.raises(SystemMessage):
        checker.check_document(document)
    document.write_text("`Missing <missing.rst>`_\n")
    with pytest.raises(ValueError, match="missing local target"):
        checker.check_document(document)
    document = tmp_path / "links.md"
    document.write_text("[Local](target.md)\n")
    checker.check_document(document)
    document.write_text("[Missing](missing.md)\n")
    with pytest.raises(ValueError, match="missing local target"):
        checker.check_document(document)
