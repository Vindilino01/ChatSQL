"""Harness de Avaliacao: mede a acuracia das Consultas contra resultados esperados.

Nao roda por padrao (precisa de um Provedor real). Para rodar:

    $env:CHATSQL_EVAL_API_KEY = "sk-..."
    $env:CHATSQL_EVAL_BASE_URL = "https://api.deepseek.com/v1"   # opcional
    $env:CHATSQL_EVAL_MODEL = "deepseek-chat"                    # opcional
    pytest tests/eval -s
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from chat_sql.engine import InMemoryDatabase
from chat_sql.pipeline import ChatSession
from chat_sql.prompt import build_fewshots
from chat_sql.provider import OpenAICompatibleProvider
from chat_sql.sample_data import generate_sample_data
from chat_sql.schema import parse_schema

EVAL_API_KEY = os.getenv("CHATSQL_EVAL_API_KEY")

pytestmark = pytest.mark.skipif(
    not EVAL_API_KEY,
    reason="defina CHATSQL_EVAL_API_KEY para rodar a Avaliacao",
)

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))


def _provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        api_key=EVAL_API_KEY or "",
        base_url=os.getenv("CHATSQL_EVAL_BASE_URL", "https://api.deepseek.com/v1"),
        model=os.getenv("CHATSQL_EVAL_MODEL", "deepseek-chat"),
    )


def _rows(result) -> list[tuple]:
    return sorted(tuple(row) for row in result.rows)


def _run_case(provider, schema_name: str, case: dict) -> tuple[bool, str]:
    ddl = (ROOT / "schemas" / f"{schema_name}.sql").read_text(encoding="utf-8")
    schema = parse_schema(ddl)
    data = generate_sample_data(schema, 50)
    database = InMemoryDatabase(schema, data)
    expected = database.execute(case["expected_sql"])

    session = ChatSession(provider, schema, database, build_fewshots(schema, None))
    proposal = session.start_question(case["question"])
    if proposal is None:
        return False, "sem Consulta valida"

    for _ in range(3):
        outcome = session.run(proposal)
        if outcome.status == "ok":
            return _rows(outcome.result) == _rows(expected), "ok"
        if outcome.status == "corrected" and outcome.proposal is not None:
            proposal = outcome.proposal
            continue
        return False, outcome.error or "falha"
    return False, "orcamento esgotado"


def test_acuracia():
    provider = _provider()
    total = 0
    passed = 0
    failures: list[str] = []
    for schema_name, cases in CASES.items():
        for case in cases:
            total += 1
            ok, detail = _run_case(provider, schema_name, case)
            if ok:
                passed += 1
            else:
                failures.append(f"[{schema_name}] {case['question']} -> {detail}")

    accuracy = passed / total if total else 0.0
    print(f"\nAcuracia: {passed}/{total} = {accuracy:.0%}")
    for failure in failures:
        print("  FALHA:", failure)

    minimum = float(os.getenv("CHATSQL_EVAL_MIN_ACCURACY", "0.5"))
    assert accuracy >= minimum
