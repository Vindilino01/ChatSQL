"""Testes-guia do importador de dump .sql (ROADMAP.md, tarefa D2). Desativados."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="Teste-guia: implemente conforme o ROADMAP.md (tarefa D2)")


def test_decode_dump_falls_back_to_latin1():
    from chat_sql.sql_dump import decode_dump

    content = "CREATE TABLE t (nome TEXT); -- Jos\u00e9".encode("latin-1")
    assert "Jos\u00e9" in decode_dump(content)


def test_looks_like_dump():
    from chat_sql.sql_dump import looks_like_dump

    text = "CREATE TABLE t (id INTEGER); INSERT INTO t VALUES (1);"
    assert looks_like_dump(text) is True
    assert looks_like_dump("SELECT 1;") is False
