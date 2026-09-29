from __future__ import annotations

import pytest

from chat_sql.guard import clean_sql, validate

ALLOWED = [
    "SELECT COUNT(*) FROM clientes;",
    "SELECT nome FROM clientes;",
    "SELECT * FROM clientes LIMIT 5;",
    "SELECT c.nome, p.valor_total FROM clientes c JOIN pedidos p ON c.id = p.cliente_id;",
    "SELECT COUNT(*) FROM clientes UNION SELECT COUNT(*) FROM clientes;",
    "WITH t AS (SELECT id FROM clientes) SELECT COUNT(*) FROM t;",
    "SELECT nome AS n FROM clientes ORDER BY n;",
    "SELECT COUNT(*) FROM pedidos WHERE data_pedido >= date('now', '-1 month');",
]

BLOCKED = [
    "DROP TABLE clientes;",
    "INSERT INTO clientes (nome) VALUES ('x');",
    "UPDATE clientes SET nome = 'x';",
    "DELETE FROM clientes;",
    "CREATE TABLE t (id INTEGER);",
    "ALTER TABLE clientes ADD COLUMN x TEXT;",
    "PRAGMA table_info(clientes);",
    "ATTACH DATABASE 'x.db' AS x;",
    "SELECT * FROM clientes; DELETE FROM clientes;",
    "SELECT load_extension('x');",
    "SELECT writefile('x', 'y');",
    "SELECT * FROM tabela_inexistente;",
    "SELECT coluna_falsa FROM clientes;",
    "SELECT c.coluna_falsa FROM clientes c;",
    "",
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_allows_read_only(sql, schema):
    result = validate(sql, schema)
    assert result.ok, result.error


@pytest.mark.parametrize("sql", BLOCKED)
def test_blocks_unsafe_or_unknown(sql, schema):
    result = validate(sql, schema)
    assert not result.ok
    assert result.error


def test_clean_sql_strips_code_fence():
    assert clean_sql("```sql\nSELECT 1;\n```") == "SELECT 1;"


def test_clean_sql_strips_label():
    assert clean_sql("SQL: SELECT 1;") == "SELECT 1;"


def test_unknown_table_message_lists_tables(schema):
    result = validate("SELECT * FROM fantasma;", schema)
    assert not result.ok
    assert "clientes" in result.error


def test_hallucinated_column_message_is_precise(schema):
    result = validate("SELECT c.faturamento FROM clientes c;", schema)
    assert not result.ok
    assert "faturamento" in result.error
    assert "nome" in result.error
