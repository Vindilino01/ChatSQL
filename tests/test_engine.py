from __future__ import annotations

import pytest

from chat_sql.engine import InMemoryDatabase, QueryError


def test_executes_select(database):
    result = database.execute("SELECT COUNT(*) FROM clientes;")
    assert result.rows[0][0] == 50
    assert result.truncated is False


def test_truncates_at_max_rows(database):
    result = database.execute("SELECT * FROM clientes;", max_rows=10)
    assert len(result.rows) == 10
    assert result.truncated is True


def test_query_only_blocks_writes(database):
    with pytest.raises(QueryError):
        database.execute("INSERT INTO clientes (nome) VALUES ('x');")


def test_invalid_sql_raises(database):
    with pytest.raises(QueryError):
        database.execute("SELECT * FROM tabela_inexistente;")


def test_script_with_inserts_uses_own_data():
    from chat_sql.schema import parse_schema

    ddl = (
        "CREATE TABLE t (id INTEGER PRIMARY KEY, nome TEXT);"
        "INSERT INTO t (id, nome) VALUES (1, 'a'), (2, 'b');"
    )
    schema = parse_schema(ddl)
    db = InMemoryDatabase(schema)
    result = db.execute("SELECT COUNT(*) FROM t;")
    assert result.rows[0][0] == 2
