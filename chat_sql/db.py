"""Conector somente leitura para bancos reais.

Implementação de referência (Fase 1 do ROADMAP.md). Cobre **SQLite** (usado nos
testes) e **Postgres** (SGBD da demonstração). Evoluções ficam com o grupo:
MySQL, mais dialetos, seletor de tabelas na tela e teste de conexão.

Como funciona
-------------
1. `DatabaseSource` abre uma engine SQLAlchemy a partir da URL fornecida.
2. Introspecta o schema (tabelas, colunas, tipos e FKs) e monta um `Schema`.
3. Em `execute()`, a Consulta passa pela Trava (`guard.validate`, no dialeto da
   fonte) e só então é executada, com limite de tempo e de linhas.

Segurança (obrigatório)
-----------------------
- Use um usuário de banco **somente leitura**.
- A Trava bloqueia DDL/DML, mas não confie apenas nela: o usuário read-only é a
  última linha de defesa.
- Sessão em modo leitura quando o dialeto permite; timeout por dialeto.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from sqlalchemy import create_engine, inspect, text
from sqlalchemy import types as sa_types
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from .config import MAX_FETCH_ROWS, QUERY_TIMEOUT_SECONDS
from .engine import QueryError, QueryTimeoutError, QueryResult
from .guard import validate
from .nl.dialect import normalize_name
from .nl.text import plural, singular
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


# Custo em idas e voltas de rede: a intropecção em massa faz 1 consulta por
# aspecto (tabelas, colunas, PKs, FKs) em vez de 3 por tabela. Em banco remoto
# isso é a diferença entre 21 idas e voltas e 4.
def _introspect(engine: Engine, schema_name: str | None = None) -> Schema:
    """Lê o banco e monta o Schema da Sessão (tabelas, colunas e FKs).

    Usa consultas em massa ao catálogo (uma por aspecto), em vez de chamar o
    inspetor do SQLAlchemy tabela por tabela. Um banco com 20 tabelas passa de
    60 idas e voltas para 4.
    """
    schema = schema_name or "public"
    dialect = engine.dialect.name

    with engine.connect() as conn:
        if dialect == "postgresql":
            tabelas = [row[0] for row in conn.exec_driver_sql(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = %s AND table_type = 'BASE TABLE' "
                "ORDER BY table_name",
                (schema,),
            )]
            colunas = conn.exec_driver_sql(
                """
                SELECT table_name, column_name, data_type, is_nullable, ordinal_position
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position
                """,
                (schema,),
            ).fetchall()
            pks = conn.exec_driver_sql(
                """
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_name = tc.constraint_name
                 AND kcu.table_schema = tc.table_schema
                WHERE tc.table_schema = %s AND tc.constraint_type = 'PRIMARY KEY'
                """,
                (schema,),
            ).fetchall()
            fks = conn.exec_driver_sql(
                """
                SELECT kcu.table_name, kcu.column_name,
                       ccu.table_name, ccu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_name = tc.constraint_name
                 AND kcu.table_schema = tc.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                WHERE tc.table_schema = %s AND tc.constraint_type = 'FOREIGN KEY'
                """,
                (schema,),
            ).fetchall()
            pk_map: dict[str, set[str]] = {}
            for tabela, coluna in pks:
                pk_map.setdefault(tabela, set()).add(coluna)
            fk_map: dict[str, list[tuple[str, str, str]]] = {}
            for origem, origem_col, destino, destino_col in fks:
                fk_map.setdefault(origem, []).append((origem_col, destino, destino_col))
        else:
            # Fallback (SQLite nos testes): usa o inspetor, que é barato local.
            inspector = inspect(engine)
            tabelas = inspector.get_table_names(schema=schema_name)
            colunas = []
            pk_map = {}
            fk_map = {}
            for tabela in tabelas:
                for coluna in inspector.get_columns(tabela, schema=schema_name):
                    colunas.append(
                        (tabela, coluna["name"], coluna["type"].__class__.__name__.lower(),
                         "YES" if coluna.get("nullable", True) else "NO", 0)
                    )
                pk_map[tabela] = set(
                    inspector.get_pk_constraint(tabela, schema=schema_name).get("constrained_columns") or []
                )
                for fk in inspector.get_foreign_keys(tabela, schema=schema_name):
                    for c, r in zip(fk.get("constrained_columns") or (), fk.get("referred_columns") or ()):
                        fk_map.setdefault(tabela, []).append((c, fk.get("referred_table"), r))

    return _montar_schema(tabelas, colunas, pk_map, fk_map)


_TIPO_CANONICO = {
    "bigint": "INTEGER", "integer": "INTEGER", "smallint": "INTEGER", "int": "INTEGER",
    "numeric": "REAL", "double precision": "REAL", "real": "REAL", "money": "REAL",
    "boolean": "BOOLEAN", "bool": "BOOLEAN",
    "date": "DATE",
    "timestamp with time zone": "TIMESTAMP", "timestamp without time zone": "TIMESTAMP",
    "datetime": "TIMESTAMP",
    "bytea": "BLOB", "blob": "BLOB",
}


def _montar_schema(tabelas, colunas, pk_map, fk_map) -> Schema:
    """Monta o Schema a partir dos dados já lidos do catálogo."""
    por_tabela: dict[str, list[tuple[str, str]]] = {t: [] for t in tabelas}
    for tabela, nome, tipo, nullable, _pos in colunas:
        if tabela in por_tabela:
            por_tabela[tabela].append((nome, tipo))

    tables: dict[str, Table] = {}
    ddl_parts: list[str] = []

    for tabela in tabelas:
        pk_cols = pk_map.get(tabela, set())
        cols: list[Column] = []
        ddl_lines: list[str] = []
        for nome, tipo in por_tabela.get(tabela, []):
            canonico = _TIPO_CANONICO.get(str(tipo).lower(), "TEXT")
            cols.append(
                Column(
                    name=nome,
                    type=canonico,
                    primary_key=nome in pk_cols,
                )
            )
            ddl_lines.append(f'    "{nome}" {canonico}')

        fks: list[ForeignKey] = []
        for coluna, destino, destino_col in fk_map.get(tabela, []):
            if not destino:
                continue
            fks.append(ForeignKey(columns=(coluna,), ref_table=destino, ref_columns=(destino_col,)))
            ddl_lines.append(
                f'    FOREIGN KEY ("{coluna}") REFERENCES "{destino}" ("{destino_col}")'
            )

        tables[tabela.lower()] = Table(name=tabela, columns=cols, foreign_keys=fks)
        ddl_parts.append(f'CREATE TABLE "{tabela}" (\n' + ",\n".join(ddl_lines) + "\n);")

    ddl = "\n\n".join(ddl_parts)
    return Schema(raw_ddl=ddl, normalized_ddl=ddl, tables=tables)


_SQLGLOT_DIALECT = {"postgresql": "postgres", "mysql": "mysql", "sqlite": "sqlite"}


@dataclass
class DatabaseConfig:
    """Dados de conexão informados pela Instituição."""

    url: str
    schema_name: str | None = None
    allowed_tables: list[str] = field(default_factory=list)


class DatabaseSource:
    """Fonte de Dados apoiada em um banco real, somente leitura."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._conexao_ativa = None
        postgres = config.url.startswith(("postgresql", "postgres"))

        connect_args: dict = {}
        if postgres:
            # O pooler do Neon recusa `statement_timeout` nos parâmetros de
            # startup; só `default_transaction_read_only` é aceito lá.
            connect_args["options"] = "-c default_transaction_read_only=on"
            connect_args["connect_timeout"] = 20
            connect_args["application_name"] = "chatsql"

        try:
            self._engine = create_engine(
                config.url,
                # `pre_ping` custa uma ida e volta por consulta; `recycle`
                # resolve conexões mortas com bem menos overhead.
                pool_pre_ping=False,
                pool_size=5,
                max_overflow=5,
                pool_recycle=300,
                connect_args=connect_args,
            )
            if postgres:
                # Os SETs valem por conexão e são aplicados uma única vez,
                # no momento em que ela nasce — não a cada consulta.
                from sqlalchemy import event

                @event.listens_for(self._engine, "connect")
                def _ao_conectar(dbapi_conn, _record):  # pragma: no cover - infra
                    try:
                        cursor = dbapi_conn.cursor()
                        cursor.execute(f"SET statement_timeout = {int(QUERY_TIMEOUT_SECONDS * 1000)}")
                        cursor.execute("SET TRANSACTION READ ONLY")
                        cursor.close()
                    except Exception:
                        pass

            with self._engine.connect() as connection:
                connection.exec_driver_sql("SELECT 1")
        except SQLAlchemyError as exc:
            raise QueryError(f"Não foi possível conectar ao banco: {exc}") from exc

        schema = _introspect(self._engine, config.schema_name)
        self.rejected_tables: list[str] = []
        self.missing_tables: list[str] = []
        if config.allowed_tables:
            allowed = {name.strip().lower() for name in config.allowed_tables if name.strip()}
            available = set(schema.tables)
            # Aceita o nome exato e também o plural/singular simples
            # ("livros" -> "livro"), que é o erro mais comum ao digitar.
            resolved: set[str] = set()
            for name in allowed:
                candidate = name
                found = None
                variants = [name, singular(name), plural(name)]
                # Plurais terminados em "-es" ("autores" -> "autor") não são
                # cobertos por `singular`; tentamos a remoção direta.
                if name.endswith("es"):
                    variants.append(name[:-2])
                if name.endswith("s"):
                    variants.append(name[:-1])
                for option in variants:
                    if option in available:
                        found = option
                        break
                if found:
                    resolved.add(found)
                else:
                    self.missing_tables.append(candidate)
            self.rejected_tables = [
                key for key in available if key not in resolved
            ]
            schema = Schema(
                raw_ddl=schema.raw_ddl,
                normalized_ddl=schema.normalized_ddl,
                tables={key: table for key, table in schema.tables.items() if key in resolved},
            )
        self._schema = schema

    @property
    def schema(self) -> Schema:
        return self._schema

    @property
    def engine_dialect(self) -> str:
        """Nome do dialeto no SQLAlchemy ('postgresql', 'sqlite', 'mysql')."""
        return self._engine.dialect.name

    @property
    def dialect(self) -> str:
        """Nome do dialeto no formato usado pelo Motor Offline ('postgres'/'sqlite')."""
        return normalize_name(self.engine_dialect)

    def _sqlglot_dialect(self) -> str:
        return _SQLGLOT_DIALECT.get(self.engine_dialect, "sqlite")

    def _apply_read_only(self, connection, timeout: float) -> None:
        """Garante modo leitura. No Postgres o timeout já vem do evento connect."""
        try:
            if self.engine_dialect == "postgresql":
                # O `SET TRANSACTION READ ONLY` já foi aplicado no connect.
                # Reforçamos o modo leitura da transação corrente sem repetir
                # o statement_timeout (que custa uma ida e volta por consulta).
                connection.exec_driver_sql("SET TRANSACTION READ ONLY")
            elif self.engine_dialect == "mysql":
                connection.exec_driver_sql(f"SET SESSION MAX_EXECUTION_TIME = {int(timeout * 1000)}")
                connection.exec_driver_sql("SET SESSION TRANSACTION READ ONLY")
            elif self.engine_dialect == "sqlite":
                connection.exec_driver_sql("PRAGMA query_only = ON")
        except SQLAlchemyError:
            # Dialetos podem não suportar; a Trava e o usuário read-only continuam valendo.
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
            # Reutiliza a mesma conexão entre consultas. Abrir e fechar uma
            # conexão a cada pergunta custa ~0,45 s num banco remoto — mais que
            # a própria consulta.
            connection = self._conexao_ativa
            if connection is None or connection.closed:
                connection = self._engine.connect()
                self._conexao_ativa = connection
                self._apply_read_only(connection, timeout)

            # `text()` impede o driver de interpretar os '%' dos LIKE como
            # marcadores de parâmetro (senão: "only '%s' ... allowed").
            cursor = connection.execute(text(outcome.sql))
            fetched = cursor.fetchmany(max_rows + 1)
            truncated = len(fetched) > max_rows
            if truncated:
                fetched = fetched[:max_rows]
            columns = list(cursor.keys()) if cursor.returns_rows else []
            rows = [tuple(row) for row in fetched]
        except SQLAlchemyError as exc:
            # Em caso de erro, descarta a conexão: o estado da transação pode
            # ter ficado inválido.
            self._descartar_conexao()
            message = str(exc)
            lowered = message.lower()
            if "timeout" in lowered or "canceling statement" in lowered or "interrupted" in lowered:
                raise QueryTimeoutError(f"A Consulta excedeu o limite de {timeout:g}s.") from exc
            raise QueryError(message) from exc

        elapsed = (time.monotonic() - started) * 1000
        return QueryResult(columns=columns, rows=rows, truncated=truncated, elapsed_ms=elapsed)

    def _descartar_conexao(self) -> None:
        connection = getattr(self, "_conexao_ativa", None)
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass
        self._conexao_ativa = None

    def close(self) -> None:
        self._descartar_conexao()
        self._engine.dispose()
