"""Execucao isolada em SQLite na memoria, com defesa em profundidade."""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass

from .config import MAX_FETCH_ROWS, QUERY_TIMEOUT_SECONDS
from .sample_data import GeneratedData
from .schema import Schema


class QueryError(Exception):
    """Falha ao executar a Consulta."""


class QueryTimeoutError(QueryError):
    """Consulta excedeu o tempo limite."""


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[tuple]
    truncated: bool
    elapsed_ms: float


class InMemoryDatabase:
    """Banco efemero: cria as tabelas do DDL, popula com Dados de Exemplo e
    passa a aceitar apenas leitura via PRAGMA query_only."""

    def __init__(self, schema: Schema, data: GeneratedData | None = None) -> None:
        self._schema = schema
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.execute("PRAGMA foreign_keys = ON")
        # Executa o script cru: cria as tabelas e, se houver, roda os INSERTs colados.
        self._create_tables(schema.raw_ddl)
        if data is not None:
            self._insert_data(data)
        self._conn.commit()
        self._conn.execute("PRAGMA query_only = ON")

    @property
    def schema(self) -> Schema:
        """O Schema da Sessao desta Fonte de Dados (ver chat_sql/datasource.py)."""
        return self._schema

    def _create_tables(self, ddl: str) -> None:
        try:
            self._conn.executescript(ddl)
        except sqlite3.Error as exc:
            raise QueryError(f"Falha ao executar o script SQL: {exc}") from exc

    def _insert_data(self, data: GeneratedData) -> None:
        for table, rows in data.rows.items():
            if not rows:
                continue
            columns = list(rows[0].keys())
            column_list = ", ".join(f'"{column}"' for column in columns)
            placeholders = ", ".join(["?"] * len(columns))
            statement = f'INSERT INTO "{table}" ({column_list}) VALUES ({placeholders})'
            values = [tuple(row.get(column) for column in columns) for row in rows]
            try:
                self._conn.executemany(statement, values)
            except sqlite3.Error as exc:
                raise QueryError(
                    f"Falha ao inserir Dados de Exemplo em '{table}': {exc}"
                ) from exc

    def execute(
        self,
        sql: str,
        *,
        max_rows: int = MAX_FETCH_ROWS,
        timeout: float = QUERY_TIMEOUT_SECONDS,
    ) -> QueryResult:
        deadline = time.monotonic() + timeout

        def _abort_when_late() -> int:
            return 1 if time.monotonic() > deadline else 0

        self._conn.set_progress_handler(_abort_when_late, 1000)
        started = time.monotonic()
        try:
            cursor = self._conn.execute(sql)
            rows = cursor.fetchmany(max_rows + 1)
            truncated = len(rows) > max_rows
            if truncated:
                rows = rows[:max_rows]
            columns = [description[0] for description in cursor.description] if cursor.description else []
        except sqlite3.OperationalError as exc:
            message = str(exc)
            if "interrupted" in message.lower():
                raise QueryTimeoutError(f"A Consulta excedeu o limite de {timeout:g}s.") from exc
            raise QueryError(message) from exc
        except sqlite3.Error as exc:
            raise QueryError(str(exc)) from exc
        finally:
            self._conn.set_progress_handler(None, 0)

        elapsed = (time.monotonic() - started) * 1000
        return QueryResult(columns=columns, rows=rows, truncated=truncated, elapsed_ms=elapsed)

    def close(self) -> None:
        try:
            self._conn.close()
        except sqlite3.Error:
            pass
