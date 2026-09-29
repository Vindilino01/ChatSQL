from __future__ import annotations

import io

import pandas as pd
import pytest

from chat_sql.engine import InMemoryDatabase
from chat_sql.guard import validate
from chat_sql.offline import OfflineEngine
from chat_sql.spreadsheet import read_tables, tables_to_data, tables_to_schema


def _csv_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def test_reads_brazilian_csv():
    files = [
        (
            "vendas.csv",
            _csv_bytes("cliente;valor;data\nAna;1.234,50;15/01/2025\nBob;2.000,00;20/02/2025\n"),
        )
    ]
    tables = read_tables(files)
    assert len(tables) == 1
    assert tables[0].name == "vendas"
    frame = tables[0].frame
    assert frame["valor"].tolist() == [1234.5, 2000.0]
    assert pd.api.types.is_datetime64_any_dtype(frame["data"])


def test_drops_unnamed_index_column():
    files = [
        (
            "vendas.csv",
            _csv_bytes(",data,cliente,valor\n0,15/01/2025,Ana,100\n1,20/01/2025,Bob,200\n"),
        )
    ]
    tables = read_tables(files)
    assert list(tables[0].frame.columns) == ["data", "cliente", "valor"]


def test_empty_csv_raises_friendly_error():
    with pytest.raises(ValueError, match="vazio"):
        read_tables([("vazio.csv", b"")])


def test_numeric_column_with_missing_values():
    files = [("dados.csv", _csv_bytes("valor;outro\n1,50;x\n;y\n"))]
    tables = read_tables(files)
    assert tables[0].frame["valor"].iloc[0] == 1.5


def test_infers_schema_and_foreign_key():
    files = [
        ("clientes.csv", _csv_bytes("id;nome\n1;Ana\n2;Bob\n")),
        ("pedidos.csv", _csv_bytes("id;cliente_id;valor\n1;1;100\n2;1;200\n3;2;50\n")),
    ]
    tables = read_tables(files)
    schema = tables_to_schema(tables)
    assert schema.has_table("clientes")
    assert schema.has_table("pedidos")
    fks = schema.table("pedidos").foreign_keys
    assert fks and fks[0].ref_table == "clientes"


def test_spreadsheet_data_is_queryable_offline():
    files = [
        ("clientes.csv", _csv_bytes("id;nome\n1;Ana\n2;Bob\n")),
        ("pedidos.csv", _csv_bytes("id;cliente_id;valor\n1;1;100\n2;1;200\n3;2;50\n")),
    ]
    tables = read_tables(files)
    schema = tables_to_schema(tables)
    database = InMemoryDatabase(schema, tables_to_data(tables, schema))

    engine = OfflineEngine()
    sql = engine.generate_sql("quais os maiores clientes por valor", schema)
    assert sql, engine.last_reason
    assert validate(sql, schema).ok

    rows = database.execute(sql).rows
    assert rows[0][0] == "Ana"
    assert float(rows[0][1]) == 300.0


def test_reads_xlsx():
    frame = pd.DataFrame({"produto": ["A", "B"], "preco": [10.0, 20.0]})
    buffer = io.BytesIO()
    frame.to_excel(buffer, index=False, engine="openpyxl")
    tables = read_tables([("produtos.xlsx", buffer.getvalue())])
    assert tables[0].name == "produtos"
    assert tables[0].frame["preco"].tolist() == [10.0, 20.0]
