"""Testes do conector de banco real (ROADMAP.md, Fase 1).

Cobrem SQLite (roda em qualquer maquina) e, opcionalmente, Postgres quando a
variavel de ambiente CHATSQL_POSTGRES_URL estiver definida.
"""

from __future__ import annotations

import os
import sqlite3

import pytest

from chat_sql.db import DatabaseConfig, DatabaseSource
from chat_sql.engine import QueryError


def _sqlite_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'demo.db').as_posix()}"


def _make_sqlite(tmp_path) -> str:
    connection = sqlite3.connect(tmp_path / "demo.db")
    connection.executescript(
        """
        CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT);
        CREATE TABLE pedidos (
            id INTEGER PRIMARY KEY,
            cliente_id INTEGER REFERENCES clientes(id),
            valor REAL
        );
        INSERT INTO clientes (id, nome) VALUES (1, 'Ana'), (2, 'Bob');
        INSERT INTO pedidos (id, cliente_id, valor)
            VALUES (1, 1, 100.0), (2, 1, 50.0), (3, 2, 20.0);
        """
    )
    connection.commit()
    connection.close()
    return _sqlite_url(tmp_path)


def test_schema_is_introspected(tmp_path):
    source = DatabaseSource(DatabaseConfig(url=_make_sqlite(tmp_path)))
    assert source.schema.has_table("clientes")
    assert source.schema.has_column("clientes", "nome")

    foreign_keys = source.schema.table("pedidos").foreign_keys
    assert foreign_keys and foreign_keys[0].ref_table == "clientes"
    assert foreign_keys[0].columns == ("cliente_id",)
    source.close()


def test_executes_read_only_query(tmp_path):
    source = DatabaseSource(DatabaseConfig(url=_make_sqlite(tmp_path)))

    result = source.execute("SELECT nome FROM clientes ORDER BY id;")
    assert [row[0] for row in result.rows] == ["Ana", "Bob"]
    assert result.columns == ["nome"]

    aggregate = source.execute("SELECT COUNT(*) FROM pedidos;")
    assert aggregate.rows[0][0] == 3
    source.close()


def test_blocks_writes(tmp_path):
    source = DatabaseSource(DatabaseConfig(url=_make_sqlite(tmp_path)))

    with pytest.raises(QueryError):
        source.execute("DROP TABLE clientes;")
    with pytest.raises(QueryError):
        source.execute("INSERT INTO clientes (id, nome) VALUES (3, 'X');")
    with pytest.raises(QueryError):
        source.execute("UPDATE clientes SET nome = 'Y';")
    source.close()


def test_blocks_unknown_column(tmp_path):
    source = DatabaseSource(DatabaseConfig(url=_make_sqlite(tmp_path)))

    with pytest.raises(QueryError):
        source.execute("SELECT inexistente FROM clientes;")
    source.close()


def test_allowed_tables_filter(tmp_path):
    source = DatabaseSource(
        DatabaseConfig(url=_make_sqlite(tmp_path), allowed_tables=["clientes"])
    )
    assert source.schema.has_table("clientes")
    assert not source.schema.has_table("pedidos")
    source.close()


def test_unknown_url_raises_query_error():
    url = "postgresql+psycopg://user:pass@127.0.0.1:1/naoexiste?connect_timeout=2"
    with pytest.raises(QueryError):
        DatabaseSource(DatabaseConfig(url=url))


@pytest.mark.skipif(
    not os.getenv("CHATSQL_POSTGRES_URL"),
    reason="defina CHATSQL_POSTGRES_URL para testar Postgres",
)
def test_postgres_connection():
    source = DatabaseSource(DatabaseConfig(url=os.environ["CHATSQL_POSTGRES_URL"]))
    assert source.schema.table_names()
    result = source.execute("SELECT 1 AS ok;")
    assert result.rows == [(1,)]
    source.close()
