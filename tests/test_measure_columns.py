"""Regressões do Motor Offline em schemas reais.

Casos descobertos ao conectar o app no Postgres da biblioteca, onde a
primeira coluna numérica costumava ser escolhida como "medida" mesmo quando
não faz sentido somá-la (ano, CPF, código).
"""

from __future__ import annotations

import pytest

from chat_sql.nl.engine import _is_measure_column, suggest_questions
from chat_sql.offline import OfflineEngine
from chat_sql.schema import Column, Schema, parse_schema

BIBLIOTECA = parse_schema(
    """
    CREATE TABLE editora (
        id_editora BIGINT PRIMARY KEY,
        nome TEXT NOT NULL,
        pais TEXT NOT NULL
    );
    CREATE TABLE livro (
        id_livro BIGINT PRIMARY KEY,
        titulo TEXT NOT NULL,
        isbn TEXT NOT NULL,
        ano_publicacao INTEGER NOT NULL,
        id_editora BIGINT NOT NULL,
        FOREIGN KEY (id_editora) REFERENCES editora(id_editora)
    );
    CREATE TABLE emprestimo (
        id_emprestimo BIGINT PRIMARY KEY,
        id_usuario BIGINT NOT NULL,
        id_exemplar BIGINT NOT NULL,
        data_emprestimo DATE NOT NULL,
        data_devolucao DATE
    );
    """
)


def _column(name: str, type_: str = "INTEGER", pk: bool = False) -> Column:
    return Column(name=name, type=type_, primary_key=pk)


@pytest.mark.parametrize(
    "name",
    ["id", "id_livro", "livro_id", "ano_publicacao", "data_cadastro", "cpf", "isbn", "cep"],
)
def test_non_measure_columns(name):
    assert _is_measure_column(_column(name)) is False


@pytest.mark.parametrize("name", ["valor", "preco", "quantidade", "nota", "estoque"])
def test_measure_columns(name):
    assert _is_measure_column(_column(name)) is True


def test_same_column_as_group_and_measure_does_not_produce_nonsense():
    sql = OfflineEngine().generate_sql("Quais os 5 maiores livro por ano_publicacao?", BIBLIOTECA)
    assert sql is not None
    # Não pode agrupar e somar a mesma coluna.
    assert not ("SUM" in sql and "GROUP BY" in sql)


def test_rank_without_measure_orders_instead_of_failing():
    sql = OfflineEngine().generate_sql("Quais os 5 maiores livro por ano_publicacao?", BIBLIOTECA)
    assert sql is not None
    assert "ORDER BY" in sql and "LIMIT 5" in sql


def test_aggregation_without_measure_returns_clear_error():
    """Somar um ano não faz sentido: o motor deve explicar, não inventar.

    Decisão alinhada com a correção do Jean (commit c835836): não rebaixar
    silenciosamente para listagem quando a pergunta pede uma agregação real.
    """
    engine = OfflineEngine()
    sql = engine.generate_sql("Qual o total de ano_publicacao?", BIBLIOTECA)
    assert sql is None
    assert engine.last_reason
    assert "coluna" in engine.last_reason.lower() or "numérica" in engine.last_reason.lower()


def test_suggestions_are_all_answerable():
    engine = OfflineEngine()
    for question in suggest_questions(BIBLIOTECA):
        assert engine.generate_sql(question, BIBLIOTECA), question


def test_suggestions_never_sum_a_year():
    for question in suggest_questions(BIBLIOTECA):
        assert "ano_publicacao" not in question.lower()
