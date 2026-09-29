from __future__ import annotations

from pathlib import Path

import pytest

from chat_sql.engine import InMemoryDatabase
from chat_sql.guard import validate
from chat_sql.nl.builder import SqlBuilder, find_path
from chat_sql.nl.engine import suggest_questions
from chat_sql.offline import OfflineEngine
from chat_sql.sample_data import generate_sample_data
from chat_sql.schema import parse_schema

ROOT = Path(__file__).resolve().parents[1]

ECOMMERCE_QUESTIONS = [
    "Quantos pedidos foram feitos em janeiro de 2025?",
    "Liste os clientes que comecam com Ana.",
    "Liste os clientes sem email.",
    "Quantos clientes existem por estado?",
    "Qual o produto mais caro?",
    "Quais os 5 produtos mais caros?",
    "Liste os produtos com preco entre 100 e 500.",
    "Quantos clientes cadastrados este ano?",
    "Liste os clientes ordenados por nome crescente.",
    "Quais categorias existem?",
    "Quantos pedidos no mes passado?",
    "Liste os clientes com email preenchido.",
    "Quais os 3 pedidos mais recentes?",
    "Liste os produtos com estoque maior que 500.",
]


@pytest.fixture(scope="module")
def ecommerce():
    ddl = (ROOT / "schemas" / "e-commerce.sql").read_text(encoding="utf-8")
    schema = parse_schema(ddl)
    database = InMemoryDatabase(schema, generate_sample_data(schema, 50))
    return schema, database


@pytest.mark.parametrize("question", ECOMMERCE_QUESTIONS)
def test_produces_valid_executable_sql(question, ecommerce):
    schema, database = ecommerce
    engine = OfflineEngine()
    sql = engine.generate_sql(question, schema)
    assert sql, engine.last_reason
    assert validate(sql, schema).ok
    database.execute(sql)  # nao pode levantar


def _sql_for(question, ecommerce):
    schema, _ = ecommerce
    return OfflineEngine().generate_sql(question, schema)


def test_group_count_is_not_distinct(ecommerce):
    sql = _sql_for("Quantos clientes existem por estado?", ecommerce)
    assert "COUNT(*)" in sql
    assert "COUNT(DISTINCT" not in sql
    assert "GROUP BY" in sql


def test_null_filter(ecommerce):
    assert "IS NULL" in _sql_for("Liste os clientes sem email.", ecommerce)


def test_not_null_filter(ecommerce):
    assert "IS NOT NULL" in _sql_for("Liste os clientes com email preenchido.", ecommerce)


def test_max_aggregate(ecommerce):
    assert _sql_for("Qual o produto mais caro?", ecommerce).upper().startswith("SELECT MAX")


def test_top_n_limit(ecommerce):
    sql = _sql_for("Quais os 5 produtos mais caros?", ecommerce)
    assert "ORDER BY" in sql and "LIMIT 5" in sql


def test_between_filter(ecommerce):
    assert "BETWEEN 100 AND 500" in _sql_for("Liste os produtos com preco entre 100 e 500.", ecommerce)


def test_relative_date(ecommerce):
    assert "date('now', '-1 month')" in _sql_for("Quantos pedidos no mes passado?", ecommerce)


def test_month_name_date(ecommerce):
    sql = _sql_for("Quantos pedidos foram feitos em janeiro de 2025?", ecommerce)
    assert "strftime('%m'" in sql and "2025" in sql


def test_distinct_list(ecommerce):
    assert "SELECT DISTINCT" in _sql_for("Quais categorias existem?", ecommerce)


def test_like_filter(ecommerce):
    assert "LIKE '%premium%'" in _sql_for("Liste os produtos que contem premium.", ecommerce)


def test_numeric_comparison(ecommerce):
    sql = _sql_for("Liste os produtos com estoque maior que 500.", ecommerce)
    assert "estoque" in sql and "> 500" in sql


def test_last_record(ecommerce):
    sql = _sql_for("qual foi o ultimo pedido feito?", ecommerce)
    assert "ORDER BY" in sql and "DESC" in sql and "LIMIT 1" in sql


def test_itens_pedido_is_not_ambiguous(ecommerce):
    sql = _sql_for("quantos itens de pedido existem", ecommerce)
    assert '"itens_pedido"' in sql


def test_group_by_month(ecommerce):
    sql = _sql_for("total de valor_total por mes", ecommerce)
    assert "strftime('%Y-%m'" in sql and "GROUP BY" in sql


def test_semantic_unit_maps_to_column():
    ddl = (
        "CREATE TABLE titanic (PassengerId INTEGER PRIMARY KEY, Survived INTEGER, "
        "Age REAL, Fare REAL);"
    )
    schema = parse_schema(ddl)
    engine = OfflineEngine()

    age_sql = engine.generate_sql("quantos passageiros tem menos de 20 anos?", schema)
    assert '"Age"' in age_sql and "20" in age_sql and "Survived" not in age_sql

    avg_sql = engine.generate_sql("qual a idade media dos passageiros", schema)
    assert "AVG" in avg_sql and '"Age"' in avg_sql

    fare_sql = engine.generate_sql("qual a tarifa media", schema)
    assert '"Fare"' in fare_sql


def test_explanation_is_generated(ecommerce):
    schema, _ = ecommerce
    result = OfflineEngine().analyze("quantos clientes por estado", schema)
    assert result.explanation
    assert "agrupando por estado" in result.explanation
    assert "clientes" in result.explanation


def test_single_table_fallback():
    schema = parse_schema("CREATE TABLE planilha1 (data DATE, cliente TEXT, valor REAL);")
    engine = OfflineEngine()
    assert engine.generate_sql("qual o total de valor", schema)
    assert engine.generate_sql("quantos registros", schema)
    assert engine.generate_sql("liste os clientes", schema)


def test_suggestions_are_valid_and_executable(ecommerce):
    schema, database = ecommerce
    engine = OfflineEngine()
    suggestions = suggest_questions(schema)
    assert suggestions
    for question in suggestions:
        sql = engine.generate_sql(question, schema)
        assert sql, f"{question}: {engine.last_reason}"
        assert validate(sql, schema).ok
        database.execute(sql)


# ---------------------------------------------------------------------------
# Diagnostico e robustez
# ---------------------------------------------------------------------------


def test_unknown_question_gives_diagnostics(ecommerce):
    schema, _ = ecommerce
    result = OfflineEngine().analyze("qual a previsao do tempo amanha", schema)
    assert result.sql is None
    assert result.error
    assert result.suggestions


def test_empty_question(ecommerce):
    schema, _ = ecommerce
    result = OfflineEngine().analyze("   ", schema)
    assert result.sql is None and result.error


def test_never_raises_on_junk(ecommerce):
    schema, _ = ecommerce
    engine = OfflineEngine()
    for junk in ["", "???", "!!!" * 100, "a b c d e f", "1 2 3", "por por por", "select * from"]:
        result = engine.analyze(junk, schema)
        assert result.sql is None or validate(result.sql, schema).ok


def test_ambiguous_tables_are_reported():
    ddl = (
        "CREATE TABLE cliente (id INTEGER PRIMARY KEY, nome TEXT);"
        "CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT);"
    )
    schema = parse_schema(ddl)
    result = OfflineEngine().analyze("quantos clientes existem", schema)
    assert result.sql is None
    assert set(result.ambiguous) == {"cliente", "clientes"}


# ---------------------------------------------------------------------------
# Juncao multi-hop (BFS)
# ---------------------------------------------------------------------------


def test_multi_hop_join_path():
    ddl = (
        "CREATE TABLE pais (id INTEGER PRIMARY KEY, nome TEXT);"
        "CREATE TABLE estado (id INTEGER PRIMARY KEY, nome TEXT, pais_id INTEGER, "
        "FOREIGN KEY (pais_id) REFERENCES pais(id));"
        "CREATE TABLE cidade (id INTEGER PRIMARY KEY, nome TEXT, estado_id INTEGER, "
        "FOREIGN KEY (estado_id) REFERENCES estado(id));"
    )
    schema = parse_schema(ddl)
    path = find_path(schema, ["cidade"], "pais")
    assert path is not None and len(path) == 2

    builder = SqlBuilder(schema, schema.table("cidade"))
    assert builder.ensure("pais")
    assert builder.col("pais", "nome") is not None
    assert builder.join_clause().count("JOIN") == 2
