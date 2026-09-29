"""Testes-guia do conector de banco real (ROADMAP.md, Fase 1).

Estao DESATIVADOS de proposito. Ao implementar `chat_sql/db.py`, remova o `skip`
(ou o `pytestmark`) e faca-os passar.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.skip(reason="Teste-guia: implemente conforme o ROADMAP.md (Fase 1)")


def test_database_source_reads_sqlite(tmp_path):
    from chat_sql.db import DatabaseConfig, DatabaseSource

    db_path = tmp_path / "demo.db"
    # TODO(grupo): criar a tabela e inserir linhas usando sqlite3.
    source = DatabaseSource(DatabaseConfig(url=f"sqlite:///{db_path}"))
    result = source.execute("SELECT 1;")
    assert result.rows == [(1,)]
    source.close()


def test_database_source_requires_read_only(tmp_path):
    from chat_sql.db import DatabaseConfig, DatabaseSource

    source = DatabaseSource(DatabaseConfig(url=f"sqlite:///{tmp_path / 'demo.db'}"))
    with pytest.raises(Exception):
        source.execute("DROP TABLE clientes;")
