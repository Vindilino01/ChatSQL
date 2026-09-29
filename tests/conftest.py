from __future__ import annotations

from pathlib import Path

import pytest

from chat_sql.engine import InMemoryDatabase
from chat_sql.sample_data import generate_sample_data
from chat_sql.schema import parse_schema

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"


@pytest.fixture
def ecommerce_ddl() -> str:
    return (SCHEMAS_DIR / "e-commerce.sql").read_text(encoding="utf-8")


@pytest.fixture
def rh_ddl() -> str:
    return (SCHEMAS_DIR / "rh.sql").read_text(encoding="utf-8")


@pytest.fixture
def vendas_ddl() -> str:
    return (SCHEMAS_DIR / "vendas.sql").read_text(encoding="utf-8")


@pytest.fixture
def schema(ecommerce_ddl):
    return parse_schema(ecommerce_ddl)


@pytest.fixture
def data(schema):
    return generate_sample_data(schema, 50)


@pytest.fixture
def database(schema, data):
    return InMemoryDatabase(schema, data)
