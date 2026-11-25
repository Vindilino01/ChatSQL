"""Google Sheets público: link de edição -> URL de export -> CSV -> tabela."""

from __future__ import annotations

import pytest

from chat_sql.sheets import SheetsError, export_url, read_public_sheet


def test_export_url_converts_edit_link():
    link = "https://docs.google.com/spreadsheets/d/ABC123/edit#gid=0"
    assert export_url(link) == (
        "https://docs.google.com/spreadsheets/d/ABC123/export?format=csv&gid=0"
    )


def test_export_url_without_gid():
    link = "https://docs.google.com/spreadsheets/d/ABC123/edit?usp=sharing"
    assert export_url(link) == "https://docs.google.com/spreadsheets/d/ABC123/export?format=csv"


def test_export_url_with_trailing_slash():
    link = "https://docs.google.com/spreadsheets/d/ABC123/"
    assert export_url(link).endswith("/export?format=csv")


def test_export_url_keeps_existing_export():
    link = "https://docs.google.com/spreadsheets/d/ABC123/export?format=csv"
    assert "format=csv" in export_url(link)


def test_rejects_non_sheets_url():
    with pytest.raises(SheetsError):
        export_url("https://example.com/tabela.csv")


def test_rejects_link_without_id():
    with pytest.raises(SheetsError):
        export_url("https://docs.google.com/spreadsheets/")


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _fake_urlopen(monkeypatch, body: bytes):
    import chat_sql.sheets as sheets

    chamadas: list[str] = []

    def urlopen(url, timeout=None):
        chamadas.append(url)
        return _FakeResponse(body)

    monkeypatch.setattr(sheets.urllib.request, "urlopen", urlopen)
    return chamadas


def test_read_public_sheet_returns_csv_bytes(monkeypatch):
    chamadas = _fake_urlopen(monkeypatch, b"nome,idade\nAna,30\n")
    arquivos = read_public_sheet("https://docs.google.com/spreadsheets/d/ABC/edit#gid=0")

    assert len(arquivos) == 1
    nome, conteudo = arquivos[0]
    assert nome.endswith(".csv")
    assert b"Ana,30" in conteudo
    assert chamadas[0].startswith("https://docs.google.com/spreadsheets/d/ABC/export")


def test_read_public_sheet_rejects_login_page(monkeypatch):
    _fake_urlopen(monkeypatch, b"<!DOCTYPE html><html><body>Faca login</body></html>")
    with pytest.raises(SheetsError) as exc:
        read_public_sheet("https://docs.google.com/spreadsheets/d/ABC/edit")
    assert "publica" in str(exc.value).replace("ú", "u")


def test_read_public_sheet_rejects_empty(monkeypatch):
    _fake_urlopen(monkeypatch, b"")
    with pytest.raises(SheetsError):
        read_public_sheet("https://docs.google.com/spreadsheets/d/ABC/edit")


def test_read_public_sheet_explains_403(monkeypatch):
    import urllib.error

    import chat_sql.sheets as sheets

    def urlopen(url, timeout=None):
        raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)

    monkeypatch.setattr(sheets.urllib.request, "urlopen", urlopen)
    with pytest.raises(SheetsError) as exc:
        read_public_sheet("https://docs.google.com/spreadsheets/d/ABC/edit")
    assert "publica" in str(exc.value).replace("ú", "u")
