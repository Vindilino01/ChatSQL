from __future__ import annotations

import json
from pathlib import Path

import pytest

from chat_sql.engine import InMemoryDatabase
from chat_sql.guard import validate
from chat_sql.offline import OfflineEngine
from chat_sql.sample_data import generate_sample_data
from chat_sql.schema import parse_schema

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests" / "eval" / "cases.json").read_text(encoding="utf-8"))
PARAMS = [
    (schema_name, index, case)
    for schema_name, items in CASES.items()
    for index, case in enumerate(items)
]


@pytest.mark.parametrize(
    "schema_name,index,case",
    PARAMS,
    ids=[f"{name}-{index}" for name, index, _ in PARAMS],
)
def test_offline_matches_expected(schema_name, index, case):
    ddl = (ROOT / "schemas" / f"{schema_name}.sql").read_text(encoding="utf-8")
    schema = parse_schema(ddl)
    database = InMemoryDatabase(schema, generate_sample_data(schema, 50))

    engine = OfflineEngine()
    sql = engine.generate_sql(case["question"], schema)
    assert sql, engine.last_reason

    result = validate(sql, schema)
    assert result.ok, result.error

    got = sorted(tuple(row) for row in database.execute(sql).rows)
    expected = sorted(tuple(row) for row in database.execute(case["expected_sql"]).rows)
    assert got == expected


def test_offline_unknown_question_returns_none(schema):
    engine = OfflineEngine()
    assert engine.generate_sql("qual a previsao do tempo amanha", schema) is None
    assert engine.last_reason
