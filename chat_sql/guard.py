"""A Trava: validacao obrigatoria antes de qualquer execucao.

Camadas:
1. Sintaxe (sqlglot).
2. Uma unica instrucao.
3. Allowlist estrita: apenas SELECT (inclui WITH/CTE e UNION).
4. Funcoes perigosas proibidas.
5. Consciencia do schema: tabelas e colunas referenciadas precisam existir.
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from .schema import Schema


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    sql: str | None = None
    error: str | None = None


_DANGEROUS_FUNCTIONS = {
    "load_extension",
    "writefile",
    "readfile",
    "edit",
    "fts3_tokenizer",
    "sqlite_readfile",
}

_PSEUDO_COLUMNS = {"rowid", "oid", "_rowid_"}

_READ_ONLY_TYPES = tuple(
    node_type
    for node_type in (
        getattr(exp, "Select", None),
        getattr(exp, "SetOperation", None),
        getattr(exp, "Union", None),
        getattr(exp, "Intersect", None),
        getattr(exp, "Except", None),
    )
    if node_type is not None
)


def clean_sql(text: str | None) -> str:
    """Remove cercas de markdown e rotulos comuns que o modelo possa devolver."""
    if not text:
        return ""
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        while lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    lowered = value.lower()
    for prefix in ("sql:", "consulta:", "query:"):
        if lowered.startswith(prefix):
            value = value[len(prefix):].strip()
            break
    return value


def _is_read_only(stmt: exp.Expression) -> bool:
    return isinstance(stmt, _READ_ONLY_TYPES)


def _find_dangerous_function(stmt: exp.Expression) -> str | None:
    for node in stmt.walk():
        name = ""
        if isinstance(node, exp.Anonymous):
            name = str(node.this)
        elif isinstance(node, exp.Func):
            try:
                name = node.sql_name()
            except Exception:
                name = type(node).__name__
        if name and name.lower() in _DANGEROUS_FUNCTIONS:
            return name
    return None


def _output_columns(query: exp.Expression) -> set[str]:
    outputs: set[str] = set()
    for select in query.find_all(exp.Select):
        for projection in select.expressions:
            if isinstance(projection, exp.Alias):
                outputs.add(projection.alias.lower())
            elif isinstance(projection, exp.Column):
                outputs.add(projection.name.lower())
    return outputs


def _check_schema(stmt: exp.Expression, schema: Schema) -> str | None:
    cte_names: set[str] = set()
    cte_outputs: dict[str, set[str]] = {}
    with_expr = stmt.args.get("with_") or stmt.args.get("with")
    if isinstance(with_expr, exp.With):
        for cte in with_expr.expressions:
            if isinstance(cte, exp.CTE):
                name = cte.alias_or_name.lower()
                cte_names.add(name)
                cte_outputs[name] = _output_columns(cte.this)

    alias_to_table: dict[str, tuple[str, str]] = {}
    referenced_tables: set[str] = set()
    select_aliases: set[str] = set()
    subquery_aliases: set[str] = set()

    for node in stmt.walk():
        if isinstance(node, exp.Alias) and node.alias:
            select_aliases.add(node.alias.lower())
        if isinstance(node, exp.Subquery) and node.alias:
            subquery_aliases.add(node.alias.lower())
        if isinstance(node, exp.Table):
            name = node.name.lower()
            alias = (node.alias or name).lower()
            if name in cte_names:
                alias_to_table[alias] = ("cte", name)
                alias_to_table.setdefault(name, ("cte", name))
            else:
                referenced_tables.add(name)
                alias_to_table[alias] = ("table", name)
                alias_to_table.setdefault(name, ("table", name))

    for name in sorted(referenced_tables):
        if not schema.has_table(name):
            available = ", ".join(schema.table_names())
            return f"A tabela '{name}' nao existe no Schema da Sessao. Tabelas disponiveis: {available}."

    available_columns: set[str] = set()
    for kind, base in alias_to_table.values():
        if kind == "table":
            available_columns.update(c.lower() for c in schema.column_names(base))
        else:
            available_columns.update(cte_outputs.get(base, set()))
    for outputs in cte_outputs.values():
        available_columns.update(outputs)

    for node in stmt.find_all(exp.Column):
        if isinstance(node.this, exp.Star):
            continue
        column = node.name
        if not column or column == "*":
            continue
        qualifier = (node.table or "").lower()
        if qualifier:
            if qualifier in subquery_aliases or qualifier in select_aliases:
                continue
            entry = alias_to_table.get(qualifier)
            if entry is None:
                continue
            kind, base = entry
            if kind == "cte":
                outputs = cte_outputs.get(base, set())
                if outputs and column.lower() not in outputs:
                    available = ", ".join(sorted(outputs))
                    return f"A coluna '{column}' nao existe em '{base}'. Colunas disponiveis: {available}."
            elif not schema.has_column(base, column):
                available = ", ".join(schema.column_names(base))
                return f"A coluna '{column}' nao existe em '{base}'. Colunas disponiveis: {available}."
        else:
            lowered = column.lower()
            if lowered in select_aliases or lowered in _PSEUDO_COLUMNS:
                continue
            if available_columns and lowered not in available_columns:
                available = ", ".join(sorted(available_columns))
                return f"A coluna '{column}' nao existe no Schema da Sessao. Colunas disponiveis: {available}."
    return None


def validate(raw_sql: str | None, schema: Schema) -> GuardResult:
    """Valida uma Consulta. Retorna GuardResult(ok=True, sql=...) se aprovada."""
    sql = clean_sql(raw_sql)
    if not sql:
        return GuardResult(False, error="A Consulta esta vazia.")

    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except ParseError as exc:
        return GuardResult(False, error=f"Erro de sintaxe SQL: {exc}")

    statements = [stmt for stmt in statements if stmt is not None]
    if not statements:
        return GuardResult(False, error="Nenhuma instrucao SQL encontrada.")
    if len(statements) > 1:
        return GuardResult(False, error="Apenas uma instrucao por Consulta e permitida.")

    stmt = statements[0]
    if not _is_read_only(stmt):
        return GuardResult(
            False,
            error=f"Somente SELECT e permitido (recebido: {type(stmt).__name__}).",
        )

    dangerous = _find_dangerous_function(stmt)
    if dangerous:
        return GuardResult(False, error=f"Funcao proibida: {dangerous}().")

    problem = _check_schema(stmt, schema)
    if problem:
        return GuardResult(False, error=problem)

    return GuardResult(True, sql=sql)
