"""Prova que um visitante consegue usar o projeto a partir de um clone limpo.

Este teste responde à pergunta: "qualquer pessoa que baixe o repositório
consegue instalar, conectar e perguntar?".

Roda quando `CHATSQL_SEED_URL` está definida (banco de demonstração). É o mesmo
caminho que a documentação manda seguir:

    pip install -r requirements.txt
    streamlit run app.py
    -> aba Dados -> Banco de dados -> colar a URL -> Conectar

O teste automatiza apenas a parte verificável: que a URL de conexão informada
funciona, que o schema é lido e que a pergunta mais simples responde com o
número esperado, dentro de um tempo aceitável.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

from chat_sql.db import DatabaseConfig, DatabaseSource
from chat_sql.offline import OfflineEngine

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
URL = os.getenv("CHATSQL_SEED_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="defina CHATSQL_SEED_URL para o teste de onboarding"
)

# O que a documentação promete ao visitante.
TEMPO_MAXIMO_CONEXAO = 25.0  # inclui cold start do Neon
TEMPO_MAXIMO_CONSULTA = 2.0


@pytest.fixture(scope="module")
def source():
    url = (URL or "").replace("postgresql://", "postgresql+psycopg://", 1)
    src = DatabaseSource(DatabaseConfig(url=url))
    yield src
    src.close()


def test_conexao_rapida(source):
    """Conectar não pode parecer travamento."""
    inicio = time.monotonic()
    url = (URL or "").replace("postgresql://", "postgresql+psycopg://", 1)
    outra = DatabaseSource(DatabaseConfig(url=url))
    decorrido = time.monotonic() - inicio
    outra.close()

    assert decorrido < TEMPO_MAXIMO_CONEXAO, (
        f"conectar levou {decorrido:.1f}s (limite {TEMPO_MAXIMO_CONEXAO}s)"
    )


def test_schema_tem_as_tabelas_da_documentacao(source):
    """O README promete 7 tabelas; se mudar, a documentação está errada."""
    esperadas = {"livro", "autor", "editora", "livro_autor", "exemplar", "usuario", "emprestimo"}
    assert set(source.schema.table_names()) == esperadas


def test_pergunta_basica_responde(source):
    """'quantos livros existem' precisa responder a verdade, rápido."""
    engine = OfflineEngine(dialect=source.dialect)
    inicio = time.monotonic()
    sql = engine.generate_sql("quantos livros existem", source.schema)
    assert sql, engine.last_reason

    resultado = source.execute(sql)
    decorrido = time.monotonic() - inicio

    assert resultado.rows == [(456,)]
    assert decorrido < TEMPO_MAXIMO_CONSULTA, f"consulta levou {decorrido:.1f}s"


@pytest.mark.parametrize(
    "pergunta,minimo",
    [
        ("quais editoras existem", 1),
        ("quais os 5 livros mais antigos", 1),
        ("quantos emprestimos por mes", 1),
        ("quais livros com titulo Dom Casmurro", 1),
    ],
)
def test_perguntas_do_roteiro_de_demo(source, pergunta, minimo):
    """As perguntas exibidas na apresentação precisam funcionar."""
    engine = OfflineEngine(dialect=source.dialect)
    sql = engine.generate_sql(pergunta, source.schema)
    assert sql, f"{pergunta}: {engine.last_reason}"
    resultado = source.execute(sql)
    assert len(resultado.rows) >= minimo, f"{pergunta} não retornou linhas"


def test_banco_de_demonstracao_e_somente_leitura(source):
    """O visitante não pode apagar dados da demonstração."""
    from chat_sql.engine import QueryError

    with pytest.raises(QueryError):
        source.execute("DELETE FROM livro WHERE id_livro = 1;")
