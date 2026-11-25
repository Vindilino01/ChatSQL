"""Importação de dump .sql."""

from __future__ import annotations

import pytest

from chat_sql.sql_dump import (
    DumpError,
    decode_dump,
    has_create,
    is_mysql_dump,
    looks_like_dump,
    normalize_for_sqlite,
    prepare,
)


def test_decode_dump_falls_back_to_latin1():
    content = "CREATE TABLE t (nome TEXT); -- José".encode("latin-1")
    assert "José" in decode_dump(content)


def test_decode_dump_prefers_utf8():
    content = "CREATE TABLE t (nome TEXT); -- José".encode("utf-8")
    assert "José" in decode_dump(content)


def test_decode_empty_raises():
    with pytest.raises(DumpError):
        decode_dump(b"")


def test_looks_like_dump():
    text = "CREATE TABLE t (id INTEGER); INSERT INTO t VALUES (1);"
    assert looks_like_dump(text) is True
    assert looks_like_dump("SELECT 1;") is False


def test_has_create_only_structure():
    text = "CREATE TABLE t (id INTEGER);"
    assert has_create(text) is True
    assert looks_like_dump(text) is False


def test_prepare_full_dump():
    texto, descricao = prepare(b"CREATE TABLE t (id INTEGER); INSERT INTO t VALUES (1);")
    assert "CREATE TABLE" in texto
    assert "dados" in descricao


def test_prepare_structure_only():
    texto, descricao = prepare(b"CREATE TABLE t (id INTEGER);")
    assert "estrutura" in descricao


def test_prepare_without_create_raises():
    with pytest.raises(DumpError):
        prepare(b"INSERT INTO t VALUES (1);")


# --- dump MySQL: o caso real de migração ------------------------------------


MYSQL_DUMP = """-- MySQL dump 10.13  Distrib 8.0.36
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
DROP TABLE IF EXISTS `clientes`;
CREATE TABLE `clientes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(120) NOT NULL,
  `cidade` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_nome` (`nome`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4;

INSERT INTO `clientes` VALUES (1,'Ana','Recife'),(2,'Bob','Natal');

CREATE TABLE `pedidos` (
  `id` int(11) NOT NULL,
  `cliente_id` int(11) NOT NULL,
  `valor` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_cliente` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `pedidos` VALUES (1,1,120.50),(2,2,80.00);
"""


def test_detects_mysql_dump():
    assert is_mysql_dump(MYSQL_DUMP) is True
    assert is_mysql_dump("CREATE TABLE t (id INTEGER);") is False


def test_prepare_marks_mysql_conversion():
    texto, descricao = prepare(MYSQL_DUMP.encode("utf-8"))
    assert "MySQL" in descricao
    assert "dados" in descricao
    assert "AUTO_INCREMENT" not in texto.upper()


def test_prepare_mysql_dump_keeps_create_and_inserts():
    texto, _ = prepare(MYSQL_DUMP.encode("utf-8"))
    assert texto.upper().count("CREATE TABLE") == 2
    assert texto.upper().count("INSERT INTO") == 2
    assert "'Ana'" in texto


def test_prepare_sqlite_untouched():
    original = "CREATE TABLE t (id INTEGER); INSERT INTO t VALUES (1);"
    texto, _ = prepare(original.encode("utf-8"))
    assert texto == original


def test_normalize_leaves_unknown_dialect_alone():
    original = "CREATE TABLE t (id INTEGER); INSERT INTO t VALUES (1);"
    assert normalize_for_sqlite(original) == original


def test_mysql_dump_runs_in_memory():
    """O teste que faltava: o dump MySQL tem de carregar e trazer os dados."""
    from chat_sql.engine import InMemoryDatabase
    from chat_sql.schema import parse_schema

    texto, _ = prepare(MYSQL_DUMP.encode("utf-8"))
    schema = parse_schema(texto)
    assert set(schema.table_names()) == {"clientes", "pedidos"}

    database = InMemoryDatabase(schema, None)
    assert database.execute("SELECT COUNT(*) FROM clientes;").rows == [(2,)]
    assert database.execute("SELECT COUNT(*) FROM pedidos;").rows == [(2,)]
    assert database.execute("SELECT SUM(valor) FROM pedidos;").rows == [(200.5,)]
    assert database.execute(
        "SELECT nome FROM clientes WHERE id = 1;"
    ).rows == [("Ana",)]


def test_mysql_dump_has_no_fake_key_column():
    from chat_sql.schema import parse_schema

    texto, _ = prepare(MYSQL_DUMP.encode("utf-8"))
    schema = parse_schema(texto)
    assert "key" not in [c.lower() for c in schema.column_names("clientes")]


def test_mysql_dump_keeps_foreign_key():
    from chat_sql.schema import parse_schema

    texto, _ = prepare(MYSQL_DUMP.encode("utf-8"))
    schema = parse_schema(texto)
    fks = schema.table("pedidos").foreign_keys
    assert fks and fks[0].ref_table == "clientes"
