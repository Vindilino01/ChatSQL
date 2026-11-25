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
    database.execute(sql)  # não pode levantar erro


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
    assert "date('now'" in _sql_for("Quantos pedidos no mes passado?", ecommerce)


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


# ---------------------------------------------------------------------------
# Defeito 1 — _detect_aggregation: novas palavras para count / sum / avg
# ---------------------------------------------------------------------------

def _single_table_schema():
    return parse_schema(
        "CREATE TABLE vendas (id INTEGER PRIMARY KEY, produto TEXT, valor REAL, quantidade INTEGER);"
    )


def test_detect_aggregation_conte():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("conte quantas vendas existem", schema)
    assert sql and "COUNT" in sql


def test_detect_aggregation_contar():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("quero contar os registros de vendas", schema)
    assert sql and "COUNT" in sql


def test_detect_aggregation_some():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("some os valores das vendas", schema)
    assert sql and "SUM" in sql


def test_detect_aggregation_somar():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("preciso somar o valor total das vendas", schema)
    assert sql and "SUM" in sql


def test_detect_aggregation_quanto_foi():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("quanto foi o valor total das vendas", schema)
    assert sql and "SUM" in sql


def test_detect_aggregation_me_diga_o_total():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("me diga o total do valor das vendas", schema)
    assert sql and "SUM" in sql


def test_detect_aggregation_calcule_o_total():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("calcule o total do valor", schema)
    assert sql and "SUM" in sql


def test_detect_aggregation_montante_total():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("qual o montante total do valor das vendas", schema)
    assert sql and "SUM" in sql


def test_detect_aggregation_calcule_a_media():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("calcule a media do valor das vendas", schema)
    assert sql and "AVG" in sql


def test_detect_aggregation_calcule_a_media_de():
    schema = _single_table_schema()
    engine = OfflineEngine()
    sql = engine.generate_sql("calcule a media de valor", schema)
    assert sql and "AVG" in sql


# ---------------------------------------------------------------------------
# Defeito 2 — _find_subject: fallback de tabela única antes do loop
# ---------------------------------------------------------------------------

def test_single_table_fallback_with_no_table_name_in_question():
    """Pergunta sem o nome da tabela deve funcionar quando há só uma tabela."""
    schema = parse_schema(
        "CREATE TABLE planilha_exportacao (id INTEGER PRIMARY KEY, valor REAL, regiao TEXT);"
    )
    engine = OfflineEngine()
    # "registros" não é o nome da tabela — antes do fix, o loop não encontrava
    # e o fallback só agia quando scored estava vazio, mas o early return agora
    # garante que a tabela é escolhida imediatamente.
    sql = engine.generate_sql("quantos registros existem aqui", schema)
    assert sql and "COUNT" in sql


def test_single_table_name_collision_resolved_immediately():
    """Com uma tabela só, mesmo que a pergunta mencione algo que poderia ser
    outra tabela, o motor deve resolver sem ambiguidade."""
    schema = parse_schema(
        "CREATE TABLE dados (id INTEGER PRIMARY KEY, cliente TEXT, total REAL);"
    )
    result = OfflineEngine().analyze("liste os dados de cliente", schema)
    assert result.sql is not None, result.error
    assert result.ambiguous == []


# ---------------------------------------------------------------------------
# Defeito 3 — COMPARISON_PATTERNS: "ou igual" deve produzir >= / <=
# ---------------------------------------------------------------------------

def test_maior_ou_igual_uses_gte(ecommerce):
    sql = _sql_for("Liste os produtos com preco maior ou igual a 100.", ecommerce)
    assert ">= 100" in sql or ">=100" in sql


def test_menor_ou_igual_uses_lte(ecommerce):
    sql = _sql_for("Liste os produtos com estoque menor ou igual a 50.", ecommerce)
    assert "<= 50" in sql or "<=50" in sql


def test_maior_sem_ou_igual_uses_gt(ecommerce):
    sql = _sql_for("Liste os produtos com estoque maior que 500.", ecommerce)
    assert "> 500" in sql or ">500" in sql
    assert ">=" not in sql


def test_menor_sem_ou_igual_uses_lt(ecommerce):
    sql = _sql_for("Liste os produtos com preco menor que 50.", ecommerce)
    assert "< 50" in sql or "<50" in sql
    assert "<=" not in sql


# ---------------------------------------------------------------------------
# Defeito 4 — _build: sem coluna numérica retorna None com mensagem clara
# ---------------------------------------------------------------------------

def test_no_numeric_column_returns_error_message():
    """Quando o intent é sum/avg/min/max e nenhuma coluna numérica existe,
    o motor deve retornar um erro com mensagem orientativa, não SQL silencioso."""
    schema = parse_schema(
        "CREATE TABLE categorias (id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT);"
    )
    engine = OfflineEngine()
    result = engine.analyze("qual o total das categorias", schema)
    assert result.sql is None
    assert "coluna" in result.error.lower() or "numérica" in result.error.lower() or "calcular" in result.error.lower()


def test_no_numeric_column_error_mentions_column():
    """Mensagem de erro deve orientar o usuário a mencionar a coluna."""
    schema = parse_schema(
        "CREATE TABLE tags (id INTEGER PRIMARY KEY, nome TEXT);"
    )
    result = OfflineEngine().analyze("some as tags", schema)
    assert result.sql is None
    assert result.error


# ---------------------------------------------------------------------------
# Defeito 5 — _build: ensure antes de builder.col() no bloco de ranking
# ---------------------------------------------------------------------------

def test_top_n_ranking_without_explicit_column():
    """'os 5 mais antigos' dispara o bloco de ranking que atribui plan.order_by
    para uma coluna de data/ano; builder.ensure deve ser chamado antes de
    builder.col() para essa tabela."""
    schema = parse_schema(
        "CREATE TABLE livros (id INTEGER PRIMARY KEY, titulo TEXT, ano_publicacao INTEGER);"
    )
    engine = OfflineEngine()
    sql = engine.generate_sql("os 5 livros mais antigos", schema)
    assert sql, engine.last_reason
    assert "LIMIT 5" in sql
    assert "ORDER BY" in sql


def test_top_n_ranking_produces_valid_sql():
    """O SQL gerado pelo ranking deve ser estruturalmente válido."""
    schema = parse_schema(
        "CREATE TABLE filmes (id INTEGER PRIMARY KEY, titulo TEXT, ano INTEGER, nota REAL);"
    )
    engine = OfflineEngine()
    sql = engine.generate_sql("os 3 filmes mais recentes", schema)
    assert sql, engine.last_reason
    assert "LIMIT 3" in sql


# ---------------------------------------------------------------------------
# Defeito 6 — _extract_like_filter: valor composto só de stopwords retorna None
# ---------------------------------------------------------------------------

def test_like_filter_stopwords_only_does_not_produce_filter():
    """'contem a os' — todos os tokens são stopwords; não deve gerar LIKE."""
    schema = parse_schema(
        "CREATE TABLE produtos (id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT);"
    )
    engine = OfflineEngine()
    sql = engine.generate_sql("liste os produtos que contem a os", schema)
    # Deve gerar SQL (listagem simples), mas sem cláusula LIKE com stopwords
    assert sql
    assert "LIKE '% a os%'" not in sql
    assert "LIKE '%a os%'" not in sql


def test_like_filter_valid_value_still_works():
    """Valor com conteúdo real deve continuar gerando LIKE normalmente."""
    schema = parse_schema(
        "CREATE TABLE produtos (id INTEGER PRIMARY KEY, nome TEXT, descricao TEXT);"
    )
    engine = OfflineEngine()
    sql = engine.generate_sql("liste os produtos que contem notebook", schema)
    assert sql and "LIKE '%notebook%'" in sql
