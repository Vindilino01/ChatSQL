"""Testes-guia do Google Sheets (ROADMAP.md, tarefa D1). Desativados de proposito."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="Teste-guia: implemente conforme o ROADMAP.md (tarefa D1)")


def test_export_url_converts_edit_link():
    from chat_sql.sheets import export_url

    link = "https://docs.google.com/spreadsheets/d/ABC123/edit#gid=0"
    assert export_url(link) == "https://docs.google.com/spreadsheets/d/ABC123/export?format=csv"


def test_read_public_sheet_returns_csv_bytes():
    from chat_sql.sheets import read_public_sheet

    files = read_public_sheet("https://docs.google.com/spreadsheets/d/PUBLICA/export?format=csv")
    assert files and files[0][1]
