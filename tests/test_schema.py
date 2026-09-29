from __future__ import annotations

import pytest

from chat_sql.schema import SchemaError, parse_schema


def test_parses_tables(schema):
    assert set(schema.table_names()) == {
        "categorias",
        "clientes",
        "produtos",
        "pedidos",
        "itens_pedido",
    }


def test_parses_columns(schema):
    assert schema.column_names("clientes") == [
        "id",
        "nome",
        "email",
        "cidade",
        "estado",
        "data_cadastro",
    ]


def test_parses_primary_key(schema):
    assert schema.table("clientes").primary_keys == ["id"]


def test_parses_foreign_key(schema):
    fk = schema.table("produtos").foreign_keys[0]
    assert fk.columns == ("categoria_id",)
    assert fk.ref_table == "categorias"
    assert fk.ref_columns == ("id",)


def test_parses_multiple_foreign_keys(schema):
    refs = {fk.ref_table for fk in schema.table("itens_pedido").foreign_keys}
    assert refs == {"pedidos", "produtos"}


def test_normalized_ddl_has_create(schema):
    assert "CREATE TABLE" in schema.normalized_ddl.upper()


def test_case_insensitive_lookup(schema):
    assert schema.has_table("CLIENTES")
    assert schema.has_column("Clientes", "NOME")


def test_empty_ddl_raises():
    with pytest.raises(SchemaError):
        parse_schema("   ")


def test_no_create_table_raises():
    with pytest.raises(SchemaError):
        parse_schema("SELECT 1;")


def test_invalid_ddl_raises():
    with pytest.raises(SchemaError):
        parse_schema("this is not sql at all (((")
