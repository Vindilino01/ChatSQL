"""Parse e normalizacao do Schema da Sessao a partir de CREATE TABLE.

Usa sqlglot para extrair tabelas, colunas, tipos e chaves estrangeiras. O DDL
normalizado e o que entra no prompt; o DDL cru e o que cria as tabelas no
SQLite (preserva AUTOINCREMENT e tipos exoticos).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


class SchemaError(Exception):
    """DDL invalido ou sem nenhum CREATE TABLE."""


@dataclass(frozen=True)
class ForeignKey:
    columns: tuple[str, ...]
    ref_table: str
    ref_columns: tuple[str, ...]


@dataclass
class Column:
    name: str
    type: str
    not_null: bool = False
    primary_key: bool = False
    unique: bool = False


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    @property
    def primary_keys(self) -> list[str]:
        return [c.name for c in self.columns if c.primary_key]


@dataclass
class Schema:
    raw_ddl: str
    normalized_ddl: str
    tables: dict[str, Table]

    def table(self, name: str) -> Table | None:
        return self.tables.get(name.lower())

    def table_names(self) -> list[str]:
        return [t.name for t in self.tables.values()]

    def has_table(self, name: str) -> bool:
        return name.lower() in self.tables

    def column_names(self, table: str) -> list[str]:
        t = self.table(table)
        return [c.name for c in t.columns] if t else []

    def has_column(self, table: str, column: str) -> bool:
        t = self.table(table)
        if t is None:
            return False
        return column.lower() in {c.name.lower() for c in t.columns}


_INT_TYPES = {
    "INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT", "MEDIUMINT",
    "INT2", "INT4", "INT8", "SERIAL", "BIGSERIAL", "SMALLSERIAL",
}
_REAL_TYPES = {
    "REAL", "DOUBLE", "DOUBLE PRECISION", "FLOAT", "DECIMAL", "NUMERIC",
    "MONEY", "NUMBER", "DEC",
}
_TEXT_TYPES = {"TEXT", "VARCHAR", "CHAR", "CHARACTER", "STRING", "CLOB", "NVARCHAR", "NCHAR"}
_BLOB_TYPES = {"BLOB", "BINARY", "VARBINARY", "BYTEA"}
_BOOL_TYPES = {"BOOLEAN", "BOOL"}
_DATE_TYPES = {"DATE"}
_TIMESTAMP_TYPES = {"DATETIME", "TIMESTAMP", "TIMESTAMPTZ", "DATETIME2"}


def _canonical_type(dtype: exp.DataType | None) -> str:
    if dtype is None:
        return "TEXT"
    raw = dtype.sql(dialect="sqlite").upper().strip()
    base = raw.split("(")[0].strip()
    if base in _INT_TYPES:
        return "INTEGER"
    if base in _REAL_TYPES:
        return "REAL"
    if base in _BOOL_TYPES:
        return "BOOLEAN"
    if base in _DATE_TYPES:
        return "DATE"
    if base in _TIMESTAMP_TYPES:
        return "TIMESTAMP"
    if base in _BLOB_TYPES:
        return "BLOB"
    if base in _TEXT_TYPES:
        return "TEXT"
    return "TEXT"


def _is_table_create(stmt: exp.Expression) -> bool:
    if not isinstance(stmt, exp.Create):
        return False
    kind = str(getattr(stmt, "kind", "") or "").upper()
    if kind and kind != "TABLE":
        return False
    return isinstance(stmt.this, exp.Schema)


def _node_name(node: exp.Expression) -> str:
    if isinstance(node, (exp.Identifier, exp.Column, exp.Table)):
        return node.name
    return getattr(node, "name", "") or ""


def _parse_reference(ref: exp.Reference, columns: tuple[str, ...]) -> ForeignKey | None:
    target = ref.this
    if isinstance(target, exp.Schema):
        ref_columns = tuple(_node_name(c) for c in target.expressions)
        target = target.this
    else:
        ref_columns = tuple(_node_name(c) for c in ref.expressions)
    ref_table = target.name if isinstance(target, exp.Table) else ""
    if not ref_table:
        return None
    return ForeignKey(columns=columns, ref_table=ref_table, ref_columns=ref_columns)


def _parse_foreign_key(fk: exp.ForeignKey) -> ForeignKey | None:
    columns = tuple(_node_name(c) for c in fk.expressions)
    ref = fk.args.get("reference")
    if not isinstance(ref, exp.Reference):
        return None
    return _parse_reference(ref, columns)


def _parse_column(coldef: exp.ColumnDef) -> tuple[Column, list[ForeignKey]]:
    column = Column(name=coldef.name, type=_canonical_type(coldef.args.get("kind")))
    inline_fks: list[ForeignKey] = []
    for constraint in coldef.args.get("constraints") or []:
        kind = constraint.kind if isinstance(constraint, exp.ColumnConstraint) else constraint
        if isinstance(kind, exp.PrimaryKeyColumnConstraint):
            column.primary_key = True
        elif isinstance(kind, exp.NotNullColumnConstraint):
            column.not_null = True
        elif isinstance(kind, exp.UniqueColumnConstraint):
            column.unique = True
        elif isinstance(kind, exp.Reference):
            fk = _parse_reference(kind, (column.name,))
            if fk is not None:
                inline_fks.append(fk)
    return column, inline_fks


def _parse_table(stmt: exp.Create) -> Table:
    schema_expr = stmt.this
    assert isinstance(schema_expr, exp.Schema)
    table = Table(name=schema_expr.this.name)

    table_level_pks: list[str] = []
    foreign_keys: list[ForeignKey] = []

    def consume(element: exp.Expression) -> None:
        if isinstance(element, exp.ColumnDef):
            column, inline_fks = _parse_column(element)
            table.columns.append(column)
            foreign_keys.extend(inline_fks)
        elif isinstance(element, exp.PrimaryKey):
            table_level_pks.extend(_node_name(c) for c in element.expressions)
        elif isinstance(element, exp.ForeignKey):
            fk = _parse_foreign_key(element)
            if fk is not None:
                foreign_keys.append(fk)
        elif isinstance(element, exp.Constraint):
            for child in element.expressions:
                consume(child)

    for element in schema_expr.expressions:
        consume(element)

    for name in table_level_pks:
        for column in table.columns:
            if column.name.lower() == name.lower():
                column.primary_key = True

    table.foreign_keys = foreign_keys
    return table


def parse_schema(ddl: str) -> Schema:
    """Converte um DDL em um Schema. Levanta SchemaError se invalido."""
    if not ddl or not ddl.strip():
        raise SchemaError("O DDL esta vazio.")

    try:
        statements = sqlglot.parse(ddl, read="sqlite")
    except ParseError as exc:
        raise SchemaError(f"DDL invalido: {exc}") from exc

    tables: dict[str, Table] = {}
    normalized: list[str] = []
    for stmt in statements:
        if stmt is None or not _is_table_create(stmt):
            continue
        table = _parse_table(stmt)
        key = table.name.lower()
        if key in tables:
            raise SchemaError(f"Tabela duplicada: {table.name}")
        if not table.columns:
            raise SchemaError(f"Tabela sem colunas: {table.name}")
        tables[key] = table
        normalized.append(stmt.sql(dialect="sqlite"))

    if not tables:
        raise SchemaError("Nenhum CREATE TABLE encontrado no DDL.")

    return Schema(
        raw_ddl=ddl.strip(),
        normalized_ddl=";\n\n".join(normalized) + ";",
        tables=tables,
    )
