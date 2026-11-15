"""O mesmo plano gera SQL válido em SQLite e em Postgres.

O Motor Offline monta SQL como texto. Se o dialeto não for respeitado, funções
como `date('now')` e `strftime` quebram no Postgres — e o app falha na demo.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chat_sql.guard import validate
from chat_sql.nl.dialect import get_dialect, normalize_name
from chat_sql.offline import OfflineEngine
from chat_sql.schema import parse_schema

ROOT = Path(__file__).resolve().parents[1]
ECOMMERCE = parse_schema((ROOT / "schemas" / "e-commerce.sql").read_text(encoding="utf-8"))

# (pergunta, trecho esperado no SQLite, trecho esperado no Postgres)
CASES = [
    (
        "quantos pedidos no mes passado",
        "date('now'",
        "CURRENT_DATE - INTERVAL '1 months'",
    ),
    (
        "quantos pedidos este mes",
        "start of month",
        "date_trunc('month', CURRENT_DATE)",
    ),
    (
        "quantos pedidos este ano",
        "start of year",
        "date_trunc('year', CURRENT_DATE)",
    ),
    (
        "quantos pedidos nos ultimos 30 dias",
        "'-30 days'",
        "INTERVAL '30 days'",
    ),
    (
        "quantos pedidos em janeiro de 2025",
        "strftime('%m'",
        "to_char(",
    ),
]

SQLITE_ONLY_TOKENS = ("date('now'", "strftime(", "CAST(strftime")


def _sql(question: str, dialect: str) -> str:
    engine = OfflineEngine(dialect=dialect)
    sql = engine.generate_sql(question, ECOMMERCE)
    assert sql, f"{dialect}: {engine.last_reason}"
    return sql


@pytest.mark.parametrize("question,sqlite_part,postgres_part", CASES)
def test_dialects_differ_as_expected(question, sqlite_part, postgres_part):
    sqlite_sql = _sql(question, "sqlite")
    postgres_sql = _sql(question, "postgres")

    assert sqlite_part in sqlite_sql, sqlite_sql
    assert postgres_part in postgres_sql, postgres_sql


@pytest.mark.parametrize("question,_sqlite_part,_postgres_part", CASES)
def test_postgres_never_uses_sqlite_functions(question, _sqlite_part, _postgres_part):
    sql = _sql(question, "postgres")
    for token in SQLITE_ONLY_TOKENS:
        assert token not in sql, f"SQLite escapou no dialeto postgres: {sql}"


@pytest.mark.parametrize("question,_sqlite_part,_postgres_part", CASES)
def test_both_dialects_pass_the_guard(question, _sqlite_part, _postgres_part):
    for dialect in ("sqlite", "postgres"):
        sql = _sql(question, dialect)
        result = validate(sql, ECOMMERCE, dialect=dialect)
        assert result.ok, f"{dialect}: {result.error}"


def test_like_becomes_ilike_on_postgres():
    question = "liste os clientes que comecam com Ana"
    assert "LIKE 'ana%'" in _sql(question, "sqlite")
    assert "ILIKE 'ana%'" in _sql(question, "postgres")


def test_boolean_literal():
    assert get_dialect("sqlite").boolean(True) == "1"
    assert get_dialect("postgres").boolean(True) == "true"
    assert get_dialect("postgres").boolean(False) == "false"


def test_normalize_name():
    assert normalize_name("PostgreSQL") == "postgres"
    assert normalize_name("postgres") == "postgres"
    assert normalize_name(None) == "sqlite"
    assert normalize_name("oracle") == "sqlite"


def test_group_by_month_uses_dialect_function():
    schema = parse_schema(
        "CREATE TABLE venda (id INTEGER PRIMARY KEY, valor REAL, data DATE);"
    )
    sqlite_sql = OfflineEngine(dialect="sqlite").generate_sql("total de valor por mes", schema)
    postgres_sql = OfflineEngine(dialect="postgres").generate_sql("total de valor por mes", schema)
    assert "strftime('%Y-%m'" in sqlite_sql
    assert "to_char(" in postgres_sql and "'YYYY-MM'" in postgres_sql


def test_id_columns_are_never_measures():
    """Colunas id_* (padrão do schema da biblioteca) não podem virar 'medida'."""
    schema = parse_schema(
        "CREATE TABLE livro (id_livro INTEGER PRIMARY KEY, titulo TEXT, "
        "ano_publicacao INTEGER, id_editora INTEGER);"
        "CREATE TABLE editora (id_editora INTEGER PRIMARY KEY, nome TEXT);"
    )
    engine = OfflineEngine()
    result = engine.analyze("liste os livros", schema)
    assert result.sql
    assert '"ano_publicacao"' not in result.sql or "SUM" not in result.sql
