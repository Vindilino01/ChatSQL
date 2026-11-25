"""Acurácia do motor em dois conjuntos, contra o banco real.

- BATERIA (desenvolvimento): perguntas usadas enquanto corrigíamos o motor.
- VALIDAÇÃO (cega): perguntas escritas depois, nunca usadas no ajuste.

A comparação é por RESULTADO: o SQL do motor precisa devolver o mesmo conjunto
que o SQL de referência. Isso pega o caso perigoso — SQL que roda e não filtra.

Uso:
    .\\venv\\Scripts\\python -m pytest tests/eval/test_acuracia.py -s
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from chat_sql.db import DatabaseConfig, DatabaseSource
from chat_sql.offline import OfflineEngine
from tests.eval.bateria_cega import CASOS, NAO_DEVEM_RESPONDER
from tests.eval.coloquial import COLOQUIAL
from tests.eval.quarto_conjunto import QUARTO_CONJUNTO
from tests.eval.validacao import VALIDACAO

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
URL = os.getenv("CHATSQL_SEED_URL")

pytestmark = pytest.mark.skipif(
    not URL, reason="defina CHATSQL_SEED_URL para medir a acurácia"
)


@pytest.fixture(scope="module")
def source():
    url = (URL or "").replace("postgresql://", "postgresql+psycopg://", 1)
    src = DatabaseSource(DatabaseConfig(url=url))
    yield src
    src.close()


def _resultado(source: DatabaseSource, sql: str):
    try:
        return sorted(tuple(r) for r in source.execute(sql).rows)
    except Exception:
        return None


def _medir(source, casos) -> tuple[int, list[str]]:
    engine = OfflineEngine(dialect=source.dialect)
    acertos = 0
    falhas: list[str] = []
    for pergunta, referencia in casos:
        esperado = _resultado(source, referencia)
        sql = engine.generate_sql(pergunta, source.schema)
        if not sql:
            falhas.append(f"{pergunta} -> não entendeu: {engine.last_reason}")
            continue
        if _resultado(source, sql) == esperado:
            acertos += 1
        else:
            falhas.append(f"{pergunta}\n    gerado: {sql}")
    return acertos, falhas


def test_acuracia_bateria(source):
    casos = [(q, r) for q, r, _categoria in CASOS]
    acertos, falhas = _medir(source, casos)
    print(f"\nBateria (desenvolvimento): {acertos}/{len(casos)} = {acertos / len(casos):.0%}")
    for f in falhas:
        print("  FALHA:", f)
    assert acertos / len(casos) >= 0.9


def test_acuracia_validacao_cega(source):
    """O número honesto: perguntas nunca usadas no ajuste do motor."""
    acertos, falhas = _medir(source, VALIDACAO)
    print(f"\nValidação (cega): {acertos}/{len(VALIDACAO)} = {acertos / len(VALIDACAO):.0%}")
    for f in falhas:
        print("  FALHA:", f)
    assert acertos / len(VALIDACAO) >= 0.85


def test_acuracia_quarto_conjunto(source):
    """Escrito só com o dicionário de dados, sem abrir o código do motor."""
    acertos, falhas = _medir(source, QUARTO_CONJUNTO)
    print(f"\nQuarto conjunto: {acertos}/{len(QUARTO_CONJUNTO)} = {acertos / len(QUARTO_CONJUNTO):.0%}")
    for f in falhas:
        print("  FALHA:", f)
    assert acertos / len(QUARTO_CONJUNTO) >= 0.85


def test_acuracia_coloquial(source):
    """Linguagem de balcão, como um funcionário falaria."""
    casos = [(q, r) for q, r in COLOQUIAL if r != "__RECUSAR__"]
    acertos, falhas = _medir(source, casos)
    print(f"\nColoquial: {acertos}/{len(casos)} = {acertos / len(casos):.0%}")
    for f in falhas:
        print("  FALHA:", f)
    assert acertos / len(casos) >= 0.85


def test_recusa_perguntas_fora_do_dominio(source):
    engine = OfflineEngine(dialect=source.dialect)
    recusas = sum(
        1 for pergunta in NAO_DEVEM_RESPONDER
        if not engine.generate_sql(pergunta, source.schema)
    )
    assert recusas == len(NAO_DEVEM_RESPONDER), "deveria recusar perguntas fora do domínio"
