"""Montagem de prompts: instrucoes defensivas em ingles, Pares de Exemplos em PT-BR."""

from __future__ import annotations

import json

from .config import FEWSHOT_MAX
from .provider import LLMProvider, ProviderError
from .schema import Schema

SYSTEM_PROMPT = """You are an expert SQLite query generator. Given a database schema and a user's question in natural language, produce exactly one read-only SELECT query that answers the question.

Rules:
- Return ONLY the SQL query. No explanations, no comments, no markdown code fences.
- Use exactly one statement.
- Only SELECT is allowed. Never write INSERT, UPDATE, DELETE, DDL, PRAGMA, ATTACH or transactions.
- Use only the tables and columns that exist in the schema. Never invent identifiers.
- Use SQLite syntax.
- Prefer explicit JOIN ... ON over implicit joins.
- For time ranges, use SQLite date functions such as date('now', '-1 month').
- If the question is ambiguous, choose the most reasonable interpretation."""

FEWSHOT_INSTRUCTION = """You write example question/answer pairs for a text-to-SQL assistant.

Schema:
{schema_ddl}

Produce {count} examples in Brazilian Portuguese. Each example has a natural-language question ("pergunta") and a valid SQLite SELECT query ("sql") that answers it using only the tables and columns above.
Cover these patterns when the schema allows: a JOIN between two tables, an aggregation (COUNT/SUM/AVG with GROUP BY), and a date filter (for example "no mes passado").

Return ONLY a JSON array, with no markdown fences, in this exact shape:
[{{"pergunta": "...", "sql": "..."}}]"""


def validation_feedback(error: str) -> str:
    return (
        "The previous query was rejected by a validator and was NOT executed.\n"
        f"Reason: {error}\n"
        "Return a corrected query that respects the rules. Return only the SQL."
    )


def execution_feedback(error: str) -> str:
    return (
        "The previous query passed validation but failed when executed by SQLite.\n"
        f"Error: {error}\n"
        "Return a corrected query. Return only the SQL."
    )


def build_messages(schema: Schema, fewshots: list[tuple[str, str]], question: str) -> list[dict]:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if fewshots:
        lines = ["Schema:", schema.normalized_ddl, "", "Examples:"]
        for example_question, example_sql in fewshots:
            lines.append(f"Question: {example_question}")
            lines.append(f"SQL: {example_sql}")
        messages.append({"role": "system", "content": "\n".join(lines)})
    messages.append({"role": "user", "content": question})
    return messages


def _parse_fewshots(raw: str) -> list[tuple[str, str]]:
    text = (raw or "").strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    pairs: list[tuple[str, str]] = []
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                question = str(item.get("pergunta") or item.get("question") or "").strip()
                sql = str(item.get("sql") or "").strip()
                if question and sql:
                    pairs.append((question, sql))
    return pairs


def build_deterministic_fewshots(schema: Schema) -> list[tuple[str, str]]:
    examples: list[tuple[str, str]] = []
    table_names = schema.table_names()
    if not table_names:
        return examples

    first = schema.table(table_names[0])
    assert first is not None
    examples.append(
        (f"Liste todos os registros de {first.name}.", f'SELECT * FROM "{first.name}" LIMIT 10;')
    )
    examples.append(
        (f"Quantos registros existem em {first.name}?", f'SELECT COUNT(*) AS total FROM "{first.name}";')
    )

    for table in schema.tables.values():
        if not table.foreign_keys:
            continue
        fk = table.foreign_keys[0]
        parent = schema.table(fk.ref_table)
        if parent is None or not fk.columns or not fk.ref_columns:
            continue
        child_column = fk.columns[0]
        parent_column = fk.ref_columns[0]
        label = next(
            (c.name for c in parent.columns if c.type == "TEXT" and not c.primary_key),
            parent.primary_keys[0] if parent.primary_keys else parent.columns[0].name,
        )
        examples.append(
            (
                f"Liste o {label} de cada {parent.name} junto com seus {table.name}.",
                (
                    f'SELECT p."{parent_column}", p."{label}", c."{child_column}" '
                    f'FROM "{table}" AS c JOIN "{parent.name}" AS p '
                    f'ON c."{child_column}" = p."{parent_column}" LIMIT 10;'
                ),
            )
        )
        break

    for table in schema.tables.values():
        date_column = next((c.name for c in table.columns if c.type in ("DATE", "TIMESTAMP")), None)
        if date_column:
            examples.append(
                (
                    f"Quantos registros de {table.name} existem no ultimo mes?",
                    f'SELECT COUNT(*) AS total FROM "{table.name}" WHERE "{date_column}" >= date(\'now\', \'-1 month\');',
                )
            )
            break

    return examples[:FEWSHOT_MAX]


def build_fewshots(
    schema: Schema,
    provider: LLMProvider | None = None,
    count: int = FEWSHOT_MAX,
) -> list[tuple[str, str]]:
    from .guard import validate

    if provider is not None:
        try:
            raw = provider.generate(
                [{"role": "user", "content": FEWSHOT_INSTRUCTION.format(schema_ddl=schema.normalized_ddl, count=count)}],
                temperature=0.0,
            )
            pairs = _parse_fewshots(raw)
            valid = [
                (question, sql)
                for question, sql in pairs
                if question.strip() and validate(sql, schema).ok
            ]
            if valid:
                return valid[:FEWSHOT_MAX]
        except Exception:
            pass
    return build_deterministic_fewshots(schema)
