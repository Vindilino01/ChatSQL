"""Avaliação do Motor Offline no schema da biblioteca (Postgres).

Diferente de `test_eval.py` (que testa o caminho com IA), este roda de verdade
contra o banco do `.env` e mede a acurácia do motor **sem IA**.

Uso:
    .\\venv\\Scripts\\python -m pytest tests/eval/test_biblioteca.py -s

Pula automaticamente quando CHATSQL_SEED_URL não está definida.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from chat_sql.db import DatabaseConfig, DatabaseSource
from chat_sql.offline import OfflineEngine

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
URL = os.getenv("CHATSQL_SEED_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="defina CHATSQL_SEED_URL para avaliar a biblioteca"
)

# (pergunta, SQL esperado). O resultado do motor é comparado com o esperado.
CASES: list[tuple[str, str]] = [
    ("quantos livros existem", "SELECT COUNT(*) FROM livro;"),
    ("quantos autores existem", "SELECT COUNT(*) FROM autor;"),
    ("quantos usuarios existem", "SELECT COUNT(*) FROM usuario;"),
    ("quantos emprestimos existem", "SELECT COUNT(*) FROM emprestimo;"),
    ("quais editoras existem", "SELECT DISTINCT nome FROM editora;"),
    ("liste os livros", "SELECT titulo FROM livro;"),
    (
        "quantos livros existem por editora",
        # Agrupar pelo nome, não pelo id: o resultado é o mesmo, mas o id não
        # significa nada para quem lê a tabela na tela.
        "SELECT editora.nome, COUNT(*) FROM livro JOIN editora "
        "ON editora.id_editora = livro.id_editora GROUP BY editora.nome;",
    ),
    (
        "quantos emprestimos por mes",
        "SELECT to_char(data_emprestimo,'YYYY-MM'), COUNT(*) "
        "FROM emprestimo GROUP BY to_char(data_emprestimo,'YYYY-MM');",
    ),
    (
        "quantos emprestimos no mes passado",
        "SELECT COUNT(*) FROM emprestimo WHERE data_emprestimo >= "
        "(CURRENT_DATE - INTERVAL '1 months');",
    ),
    (
        "quantos emprestimos em janeiro de 2025",
        "SELECT COUNT(*) FROM emprestimo WHERE to_char(data_emprestimo,'MM') = '01' "
        "AND to_char(data_emprestimo,'YYYY') = '2025';",
    ),
    (
        "quais livros com titulo Dom Casmurro",
        "SELECT titulo FROM livro WHERE titulo ILIKE '%dom casmurro%';",
    ),
    (
        "quais livros que comecam com Dom",
        "SELECT titulo FROM livro WHERE titulo ILIKE 'dom%';",
    ),
    (
        "quais os 5 livros mais recentes",
        "SELECT ano_publicacao FROM livro ORDER BY ano_publicacao DESC LIMIT 5;",
    ),
    (
        "qual foi o ultimo emprestimo",
        "SELECT data_emprestimo FROM emprestimo ORDER BY data_emprestimo DESC LIMIT 1;",
    ),
]


def _result(source: DatabaseSource, sql: str) -> list[tuple]:
    return sorted(tuple(row) for row in source.execute(sql).rows)


@pytest.fixture(scope="module")
def source():
    url = (URL or "").replace("postgresql://", "postgresql+psycopg://", 1)
    src = DatabaseSource(DatabaseConfig(url=url))
    yield src
    src.close()


def test_acuracia_biblioteca(source):
    engine = OfflineEngine(dialect="postgres")
    passed = 0
    failures: list[str] = []

    for question, expected_sql in CASES:
        generated = engine.generate_sql(question, source.schema)
        if not generated:
            failures.append(f"{question} -> sem SQL ({engine.last_reason})")
            continue
        try:
            got = _result(source, generated)
            expected = _result(source, expected_sql)
        except Exception as exc:
            failures.append(f"{question} -> erro: {str(exc)[:80]}")
            continue
        if got == expected:
            passed += 1
        else:
            failures.append(f"{question}\n    gerado:   {generated}\n    esperado: {expected_sql}")

    total = len(CASES)
    print(f"\nAcurácia (biblioteca, sem IA): {passed}/{total} = {passed / total:.0%}")
    for failure in failures:
        print("  FALHA:", failure)

    assert passed / total >= 0.7, f"abaixo da meta de 70%: {passed}/{total}"
