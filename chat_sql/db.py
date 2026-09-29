"""Conector somente-leitura para bancos reais.

Implementacao de referencia (Fase 1 do ROADMAP.md). Cobre **SQLite** (usado nos
testes) e **Postgres** (SGBD da demonstracao). Evolucoes ficam com o grupo:
MySQL, mais dialetos, seletor de tabelas na UI e teste de conexao.

Como funciona
-------------
1. `DatabaseSource` abre uma engine SQLAlchemy a partir da URL fornecida.
2. Introspecta o schema (tabelas, colunas, tipos e FKs) e monta um `Schema`.
3. Em `execute()`, a Consulta passa pela Trava (`guard.validate`, no dialeto da
   fonte) e so entao e executada, com limite de tempo e de linhas.

Seguranca (obrigatorio)
-----------------------
- Use um usuario de banco **somente-leitura**.
- A Trava bloqueia DDL/DML, mas nao confie apenas nela: o usuario read-only e a
  ultima linha de defesa.
- Sessao em modo leitura quando o dialeto permite; timeout por dialeto.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy import create_engine, inspect
from sqlalchemy import types as sa_types
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .config import MAX_FETCH_ROWS, QUERY_TIMEOUT_SECONDS
from .engine import QueryError, QueryTimeoutError, QueryResult
from .guard import validate
from .schema import Column, ForeignKey, Schema, Table


def _canonical_type(sa_type) -> str:
    """Traduz um tipo do SQLAlchemy para os tipos canonicos do projeto."""
    if isinstance(sa_type, sa_types.Boolean):
        return "BOOLEAN"
    if isinstance(sa_type, sa_types.Integer):
        return "INTEGER"
    if isinstance(sa_type, (sa_types.Float, sa_types.Numeric, sa_types.REAL)):
        return "REAL"
    if isinstance(sa_type, sa_types.DateTime):
        return "TIMESTAMP"
    if isinstance(sa_type, sa_types.Date):
        return "DATE"
    if isinstance(sa_type, sa_types.LargeBinary):
        return "BLOB"
    return "TEXT"


def _introspect(engine: Engine, schema_name: str | None = None) -> Schema:
    """Le o banco e monta o Schema da Sessao (tabelas, colunas e FKs)."""
    inspector = inspect(engine)
    tables: dict[str, Table] = {}
    ddl_parts: list[str] = []

    for table_name in inspector.get_table_names(schema=schema_name):
        primary_keys = set(
            inspector.get_pk_constraint(table_name, schema=schema_name).get("constrained_columns") or []
        )
        columns: list[Column] = []
        ddl_lines: list[str] = []
        for column in inspector.get_columns(table_name, schema=schema_name):
            canonical = _canonical_type(column["type"])
            columns.append(
                Column(
                    name=column["name"],
                    type=canonical,
                    not_null=not column.get("nullable", True),
                    primary_key=column["name"] in primary_keys,
                )
            )
            ddl_lines.append(f'    "{column["name"]}" {canonical}')

        foreign_keys: list[ForeignKey] = []
        for fk in inspector.get_foreign_keys(table_name, schema=schema_name):
            referred_table = fk.get("referred_table") or ""
            constrained = tuple(fk.get("constrained_columns") or ())
            referred_columns = tuple(fk.get("referred_columns") or ())
            if not referred_table or not constrained:
                continue
            foreign_keys.append(
                ForeignKey(columns=constrained, ref_table=referred_table, ref_columns=referred_columns)
            )
            ddl_lines.append(
                f'    FOREIGN KEY ({", ".join(constrained)}) '
                f'REFERENCES "{referred_table}" ({", ".join(referred_columns)})'
            )

        tables[table_name.lower()] = Table(name=table_name, columns=columns, foreign_keys=foreign_keys)
        ddl_parts.append(f'CREATE TABLE "{table_name}" (\n' + ",\n".join(ddl_lines) + "\n);")

    ddl = "\n\n".join(ddl_parts)
    return Schema(raw_ddl=ddl, normalized_ddl=ddl, tables=tables)


_SQLGLOT_DIALECT = {"postgresql": "postgres", "mysql": "mysql", "sqlite": "sqlite"}


@dataclass
class DatabaseConfig:
    """Dados de conexao informados pela Instituicao."""

    url: str
    schema_name: str | None = None
    allowed_tables: list[str] = field(default_factory=list)


class DatabaseSource:
    """Fonte de Dados apoiada em um banco real, somente leitura."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        try:
            self._engine = create_engine(config.url, pool_pre_ping=True)
            with self._engine.connect() as connection:
                connection.exec_driver_sql("SELECT 1")
        except SQLAlchemyError as exc:
            raise QueryError(f"Nao foi possivel conectar ao banco: {exc}") from exc

        schema = _introspect(self._engine, config.schema_name)
        if config.allowed_tables:
            allowed = {name.lower() for name in config.allowed_tables}
            schema = Schema(
                raw_ddl=schema.raw_ddl,
                normalized_ddl=schema.normalized_ddl,
                tables={key: table for key, table in schema.tables.items() if key in allowed},
            )
        self._schema = schema

    @property
    def schema(self) -> Schema:
        return self._schema

    @property
    def dialect(self) -> str:
        return self._engine.dialect.name

    def _sqlglot_dialect(self) -> str:
        return _SQLGLOT_DIALECT.get(self.dialect, "sqlite")

    def _apply_read_only(self, connection, timeout: float) -> None:
        """Aplica modo leitura e timeout quando o dialeto permite."""
        try:
            if self.dialect == "postgresql":
                connection.exec_driver_sql(f"SET statement_timeout = {int(timeout * 1000)}")
                connection.exec_driver_sql("SET default_transaction_read_only = on")
            elif self.dialect == "mysql":
                connection.exec_driver_sql(f"SET SESSION MAX_EXECUTION_TIME = {int(timeout * 1000)}")
                connection.exec_driver_sql("SET SESSION TRANSACTION READ ONLY")
            elif self.dialect == "sqlite":
                connection.exec_driver_sql("PRAGMA query_only = ON")
        except SQLAlchemyError:
            # Dialetos podem nao suportar; a Trava e o usuario read-only continuam valendo.
            pass

    def execute(
        self,
        sql: str,
        *,
        max_rows: int = MAX_FETCH_ROWS,
        timeout: float = QUERY_TIMEOUT_SECONDS,
    ) -> QueryResult:
        outcome = validate(sql, self._schema, dialect=self._sqlglot_dialect())
        if not outcome.ok or not outcome.sql:
            raise QueryError(outcome.error or "Consulta bloqueada pela Trava.")

        started = time.monotonic()
        try:
            with self._engine.connect() as connection:
                self._apply_read_only(connection, timeout)
                cursor = connection.exec_driver_sql(outcome.sql)
                fetched = cursor.fetchmany(max_rows + 1)
                truncated = len(fetched) > max_rows
                if truncated:
                    fetched = fetched[:max_rows]
                columns = list(cursor.keys()) if cursor.returns_rows else []
                rows = [tuple(row) for row in fetched]
        except SQLAlchemyError as exc:
            message = str(exc)
            lowered = message.lower()
            if "timeout" in lowered or "canceling statement" in lowered or "interrupted" in lowered:
                raise QueryTimeoutError(f"A Consulta excedeu o limite de {timeout:g}s.") from exc
            raise QueryError(message) from exc

        elapsed = (time.monotonic() - started) * 1000
        return QueryResult(columns=columns, rows=rows, truncated=truncated, elapsed_ms=elapsed)

    def close(self) -> None:
        self._engine.dispose()
