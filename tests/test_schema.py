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


MYSQL_DUMP = """
CREATE TABLE `clientes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(120) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `pedidos` (
  `id` int(11) NOT NULL,
  `cliente_id` int(11) NOT NULL,
  `valor` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_cliente` (`cliente_id`),
  INDEX `idx_valor` (`valor`),
  CONSTRAINT `fk_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def test_mysql_dump_does_not_create_fake_key_column():
    """`KEY nome (col)` do MySQL não é coluna — é índice."""
    schema = parse_schema(MYSQL_DUMP)
    assert schema.column_names("pedidos") == ["id", "cliente_id", "valor"]


def test_mysql_dump_keeps_real_foreign_key():
    schema = parse_schema(MYSQL_DUMP)
    fks = schema.table("pedidos").foreign_keys
    assert len(fks) == 1
    assert fks[0].columns == ("cliente_id",)
    assert fks[0].ref_table == "clientes"


def test_mysql_dump_keeps_quoted_column_named_key():
    """Uma coluna de verdade chamada `key` sobrevive ao filtro."""
    schema = parse_schema("CREATE TABLE t (`key` text, id int);")
    assert schema.column_names("t") == ["key", "id"]
