"""Motor Offline: analise de perguntas em PT-BR e geracao de Consultas SQL.

Nunca lanca excecao: qualquer falha vira um OfflineResult com `error` e
`suggestions`. Quando ha mais de uma interpretacao plausivel, devolve
`ambiguous` em vez de escolher no escuro.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..schema import Column, Schema, Table
from . import lexicon as lex
from .builder import SqlBuilder
from .text import forms, normalize, plural, position, question_forms, singular

# ---------------------------------------------------------------------------
# Modelo de plano e resultado
# ---------------------------------------------------------------------------


@dataclass
class Filter:
    kind: str  # numeric, date, null, boolean, like, text
    table: str
    column: str
    operator: str
    value: object = None


@dataclass
class Plan:
    subject: Table
    intent: str = "list"  # list, count, sum, avg, min, max
    measure: tuple[Table, Column] | None = None
    group: tuple[Table, Column] | None = None
    columns: list[tuple[Table, Column]] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)
    order_by: tuple[Table, Column] | None = None
    order_desc: bool = False
    limit: int | None = None
    distinct: bool = False
    select_all: bool = False
    having: tuple[str, object] | None = None
    group_time: str | None = None  # month, year, day


@dataclass
class OfflineResult:
    sql: str | None
    understood: dict
    confidence: float
    error: str | None = None
    suggestions: list[str] = field(default_factory=list)
    ambiguous: list[str] = field(default_factory=list)
    explanation: str = ""


def _explain_plan(plan: Plan) -> str:
    measure = plan.measure[1].name if plan.measure else None
    action = {
        "count": "Contei os registros",
        "sum": f"Soma de {measure}" if measure else "Soma",
        "avg": f"Media de {measure}" if measure else "Media",
        "max": f"Maior {measure}" if measure else "Maior valor",
        "min": f"Menor {measure}" if measure else "Menor valor",
        "list": "Listei os registros",
    }.get(plan.intent, "Listei os registros")

    parts = [f"{action} de {plan.subject.name}"]
    if plan.group is not None:
        parts.append(f"agrupando por {plan.group[1].name}")

    filter_texts: list[str] = []
    for filter_ in plan.filters:
        if filter_.kind == "date":
            filter_texts.append(f"{filter_.column} ({filter_.operator})")
        elif filter_.kind == "numeric":
            filter_texts.append(f"{filter_.column} {filter_.operator} {filter_.value}")
        elif filter_.kind == "boolean":
            filter_texts.append(f"{filter_.column} = {filter_.value}")
        elif filter_.kind == "null":
            filter_texts.append(f"{filter_.column} {'nulo' if filter_.operator == 'is_null' else 'preenchido'}")
        elif filter_.kind == "like":
            filter_texts.append(f"{filter_.column} contem '{filter_.value}'")
        elif filter_.kind == "text":
            filter_texts.append(f"{filter_.column} = '{filter_.value}'")
    if filter_texts:
        parts.append("com " + ", ".join(filter_texts))

    if plan.order_desc:
        parts.append("em ordem decrescente")
    if plan.limit:
        parts.append(f"limitado a {plan.limit}")
    return ", ".join(parts) + "."


# ---------------------------------------------------------------------------
# Utilitarios de busca
# ---------------------------------------------------------------------------


def _is_measure_column(column: Column) -> bool:
    name = column.name.lower()
    return not column.primary_key and not name.endswith("_id") and name != "id"


def _column_mentioned(column: Column, q_forms: set[str]) -> bool:
    name = column.name.lower()
    if name in q_forms or singular(name) in q_forms:
        return True
    parts = name.replace("_", " ").split()
    return bool(parts) and all(part in q_forms or singular(part) in q_forms for part in parts)


def _label_column(table: Table) -> Column:
    for hint in lex.LABEL_HINTS:
        for column in table.columns:
            if column.primary_key or column.name.lower().endswith("_id"):
                continue
            if column.type in ("INTEGER", "REAL", "DATE", "TIMESTAMP", "BOOLEAN", "BLOB"):
                continue
            if hint in forms(column.name):
                return column
    for column in table.columns:
        if column.type == "TEXT" and not column.primary_key:
            return column
    for column in table.columns:
        if not column.primary_key and not column.name.lower().endswith("_id"):
            return column
    return table.columns[0]


def _date_column(table: Table) -> Column | None:
    for column in table.columns:
        if column.type in ("DATE", "TIMESTAMP"):
            return column
    return None


def _related(schema: Schema, subject: Table) -> list[Table]:
    result: list[Table] = []
    for fk in subject.foreign_keys:
        parent = schema.table(fk.ref_table)
        if parent is not None:
            result.append(parent)
    for table in schema.tables.values():
        if table.name.lower() == subject.name.lower():
            continue
        for fk in table.foreign_keys:
            if fk.ref_table.lower() == subject.name.lower():
                result.append(table)
    return result


def _find_subject(schema: Schema, question: str) -> tuple[Table | None, list[str]]:
    q_forms = question_forms(question)
    scored: list[tuple[float, Table]] = []
    for table in schema.tables.values():
        parts = [part for part in re.split(r"[_ ]+", table.name.lower()) if part]
        if not parts:
            continue
        matched = 0
        score = 0.0
        for part in parts:
            part_forms = {part, singular(part), plural(part)}
            if part_forms & q_forms:
                matched += 1
                score += 10 - min(position(question, part_forms), 9)
        if matched == 0:
            continue
        # Nome composto so pontua cheio se todas as partes aparecem; um casamento
        # parcial (ex.: "pedido" dentro de "itens_pedido") vale menos.
        if matched == len(parts):
            score += 5
        score *= matched / len(parts)
        scored.append((round(score, 3), table))
    if not scored:
        # Sem nome de tabela na pergunta: se houver so uma tabela, e ela.
        if len(schema.tables) == 1:
            return next(iter(schema.tables.values())), []
        # Senao, tenta inferir pela coluna citada.
        by_column = [
            table
            for table in schema.tables.values()
            if any(_column_mentioned(column, q_forms) for column in table.columns)
        ]
        if len(by_column) == 1:
            return by_column[0], []
        return None, []
    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_table = scored[0]
    ambiguous = [table.name for score, table in scored[1:] if abs(score - best_score) < 0.01]
    return best_table, ambiguous


# ---------------------------------------------------------------------------
# Medida e agrupamento
# ---------------------------------------------------------------------------


def _semantic_column(schema: Schema, question: str, subject: Table):
    words = set(question.split())
    candidates = [subject] + _related(schema, subject)
    for unit, names in lex.SEMANTIC_HINTS.items():
        if unit not in words and singular(unit) not in words:
            continue
        for name in names:
            for table in candidates:
                for column in table.columns:
                    if (
                        column.type in ("INTEGER", "REAL")
                        and _is_measure_column(column)
                        and name in forms(column.name)
                    ):
                        return (table, column)
    return None


def _resolve_measure(schema: Schema, question: str, subject: Table):
    candidates = [subject] + _related(schema, subject)
    q_forms = question_forms(question)
    for table in candidates:
        for column in table.columns:
            if (
                column.type in ("INTEGER", "REAL")
                and _is_measure_column(column)
                and _column_mentioned(column, q_forms)
            ):
                return (table, column)
    for keyword, preferred in lex.MEASURE_KEYWORDS.items():
        if keyword not in question:
            continue
        for wanted in preferred:
            for table in candidates:
                for column in table.columns:
                    if column.name.lower() == wanted:
                        return (table, column)
        for table in candidates:
            for column in table.columns:
                if column.type == "REAL" and _is_measure_column(column):
                    return (table, column)
    semantic = _semantic_column(schema, question, subject)
    if semantic is not None:
        return semantic
    for table in candidates:
        for column in table.columns:
            if column.type == "REAL" and _is_measure_column(column):
                return (table, column)
    for table in candidates:
        for column in table.columns:
            if column.type == "INTEGER" and _is_measure_column(column):
                return (table, column)
    return None


def _resolve_group(schema: Schema, question: str, subject: Table):
    match = re.search(
        r"\b(?:por|para cada|em cada|agrupado por|agrupada por)\s+([a-z0-9_ ]+)",
        question,
    )
    if not match:
        return None
    words = [word for word in match.group(1).split() if word not in lex.STOPWORDS]
    if not words:
        return None
    noun = words[0]
    if noun in lex.MEASURE_WORDS or noun in forms(subject.name):
        return None
    for column in subject.columns:
        if noun in forms(column.name):
            return (subject, column)
    for table in _related(schema, subject):
        for column in table.columns:
            if noun in forms(column.name):
                return (table, column)
    for table in schema.tables.values():
        if noun in forms(table.name):
            return (table, _label_column(table))
    return None


def _resolve_columns(schema: Schema, question: str, subject: Table) -> list[tuple[Table, Column]]:
    q_forms = question_forms(question)
    found: list[tuple[int, Table, Column]] = []
    candidates = [subject] + _related(schema, subject)
    for index, token in enumerate(question.split()):
        token_forms = {token, singular(token), singular(token) + "s"}
        for table in candidates:
            for column in table.columns:
                if column.type in ("INTEGER", "REAL", "BLOB"):
                    continue
                if _column_mentioned(column, token_forms):
                    found.append((index, table, column))
    seen: set[tuple[str, str]] = set()
    result: list[tuple[Table, Column]] = []
    for _, table, column in sorted(found, key=lambda item: item[0]):
        key = (table.name.lower(), column.name.lower())
        if key not in seen:
            seen.add(key)
            result.append((table, column))
    return result


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------


def _numeric_target(schema: Schema, question: str, subject: Table, measure):
    q_forms = question_forms(question)
    for table in [subject] + _related(schema, subject):
        for column in table.columns:
            if (
                column.type in ("INTEGER", "REAL")
                and _is_measure_column(column)
                and _column_mentioned(column, q_forms)
            ):
                return (table, column)
    semantic = _semantic_column(schema, question, subject)
    if semantic is not None:
        return semantic
    if measure is not None:
        return measure
    for column in subject.columns:
        if column.type in ("INTEGER", "REAL") and _is_measure_column(column):
            return (subject, column)
    return None


def _extract_numeric_filter(schema: Schema, question: str, subject: Table, measure) -> Filter | None:
    for pattern in lex.BETWEEN_PATTERNS:
        match = re.search(pattern, question)
        if match:
            column = _numeric_target(schema, question, subject, measure)
            if column is None:
                continue
            low = match.group(1).replace(",", ".")
            high = match.group(2).replace(",", ".")
            return Filter("numeric", column[0].name, column[1].name, "between", (low, high))
    for pattern, _long, short in lex.COMPARISON_PATTERNS:
        match = re.search(pattern, question)
        if not match:
            continue
        column = _numeric_target(schema, question, subject, measure)
        if column is None:
            return None
        value = match.group(1).replace(",", ".")
        return Filter("numeric", column[0].name, column[1].name, short, value)
    return None


def _extract_boolean_filter(question: str, subject: Table) -> Filter | None:
    words = set(question.split())
    target = None
    if words & lex.FALSE_WORDS:
        target = 0
    if words & lex.TRUE_WORDS:
        target = 1
    if target is None:
        return None
    for column in subject.columns:
        if "ativo" in forms(column.name) or "active" in forms(column.name):
            return Filter("boolean", subject.name, column.name, "=", target)
    return None


def _extract_null_filter(question: str, subject: Table) -> Filter | None:
    words = set(question.split())
    is_null = (
        bool(words & lex.NULL_WORDS)
        or re.search(r"\bsem\s+\w+", question) is not None
        or "nao tem" in question
        or "nao possui" in question
    )
    is_not_null = bool(words & lex.NOT_NULL_WORDS) or "com valor" in question
    if not (is_null or is_not_null):
        return None
    q_forms = question_forms(question)
    for column in subject.columns:
        if column.primary_key:
            continue
        if _column_mentioned(column, q_forms):
            operator = "is_null" if (is_null and not is_not_null) else "is_not_null"
            return Filter("null", subject.name, column.name, operator)
    return None


def _extract_like_filter(question: str, subject: Table) -> Filter | None:
    q_forms = question_forms(question)
    for pattern, mode in lex.LIKE_PATTERNS:
        match = re.search(pattern, question)
        if not match:
            continue
        value = match.group(1).strip()
        if not value or value in lex.STOPWORDS:
            continue
        for column in subject.columns:
            if column.type == "TEXT" and not column.primary_key and _column_mentioned(column, q_forms):
                return Filter("like", subject.name, column.name, mode, value)
        label = _label_column(subject)
        return Filter("like", subject.name, label.name, mode, value)
    return None


_TEXT_FILTER_PATTERN = re.compile(
    r"\b(status|situacao|tipo|categoria|segmento|genero|sexo|plano)\s+([a-z0-9_]+)"
)


def _extract_text_filter(question: str, subject: Table) -> Filter | None:
    match = _TEXT_FILTER_PATTERN.search(question)
    if not match:
        return None
    keyword, value = match.group(1), match.group(2)
    if value in lex.STOPWORDS:
        return None
    for column in subject.columns:
        if column.type == "TEXT" and keyword in forms(column.name):
            return Filter("text", subject.name, column.name, "=", value)
    return None


def _extract_date_filter(schema: Schema, question: str, subject: Table, preferred: list[Table]) -> Filter | None:
    order: list[Table] = []
    for table in preferred + [subject] + _related(schema, subject):
        if table is not None and table.name.lower() not in [t.name.lower() for t in order]:
            order.append(table)
    q_forms = question_forms(question)
    target: tuple[Table, Column] | None = None
    for table in order:
        for column in table.columns:
            if column.type in ("DATE", "TIMESTAMP") and forms(column.name) & q_forms:
                target = (table, column)
                break
        if target:
            break
    if target is None:
        for table in order:
            column = _date_column(table)
            if column is not None:
                target = (table, column)
                break
    if target is None:
        return None
    table, column = target

    match = re.search(r"ultimos? (\d+) (dias?|meses?|anos?)", question)
    if match:
        count, unit = match.group(1), match.group(2)
        unit = "days" if unit.startswith("dia") else ("months" if unit.startswith("mes") else "years")
        return Filter("date", table.name, column.name, f"last_n_{unit}", int(count))

    if "mes passado" in question or "ultimo mes" in question or "mes anterior" in question:
        return Filter("date", table.name, column.name, "last_month")
    if "mes retrasado" in question:
        return Filter("date", table.name, column.name, "last_two_months")
    if "este mes" in question or "mes atual" in question or "nesse mes" in question or "neste mes" in question:
        return Filter("date", table.name, column.name, "this_month")
    if "ano passado" in question or "ultimo ano" in question or "ano anterior" in question:
        return Filter("date", table.name, column.name, "last_year")
    if "este ano" in question or "ano atual" in question or "nesse ano" in question:
        return Filter("date", table.name, column.name, "this_year")
    if "anteontem" in question:
        return Filter("date", table.name, column.name, "days_ago", 2)
    if "ontem" in question:
        return Filter("date", table.name, column.name, "days_ago", 1)
    if "hoje" in question:
        return Filter("date", table.name, column.name, "days_ago", 0)
    if "semana passada" in question or "ultima semana" in question:
        return Filter("date", table.name, column.name, "last_n_days", 7)

    quarter = re.search(r"(primeiro|segundo|terceiro|quarto) trimestre", question)
    if quarter:
        index = {"primeiro": 1, "segundo": 2, "terceiro": 3, "quarto": 4}[quarter.group(1)]
        return Filter("date", table.name, column.name, "quarter", index)

    month_names = "|".join(sorted(list(lex.MONTHS) + list(lex.MONTH_ALIASES), key=len, reverse=True))
    month_match = re.search(r"\b(" + month_names + r")\b(?:\s+de\s+(\d{4}))?", question)
    if month_match:
        month = lex.MONTHS.get(month_match.group(1)) or lex.MONTH_ALIASES.get(month_match.group(1))
        year = int(month_match.group(2)) if month_match.group(2) else None
        return Filter("date", table.name, column.name, "month_name", (month, year))

    year_match = re.search(r"\b(19|20)\d{2}\b", question)
    if year_match:
        return Filter("date", table.name, column.name, "year", int(year_match.group(0)))

    return None


def _extract_order_limit(schema: Schema, question: str, subject: Table, measure, group):
    limit = None
    for pattern in (
        r"\btop\s+(\d+)",
        r"\blimite\s+(\d+)",
        r"\bapenas\s+(\d+)",
        r"\b(?:os|as)\s+(\d+)\b",
        r"\b(\d+)\s+(?:maiores|menores|melhores|piores|primeiros|primeiras|ultimos|ultimas)\b",
    ):
        match = re.search(pattern, question)
        if match:
            limit = int(match.group(1))
            break
    if limit is None and re.search(r"\b(maiores|menores|melhores|piores|primeiros|ultimos)\b", question):
        for token in question.split():
            if token in lex.NUMBER_WORDS:
                limit = lex.NUMBER_WORDS[token]
                break
    if limit is None and re.search(r"\b(ultimo|ultima|primeiro|primeira)\b", question) and not re.search(r"\b\d+\b", question):
        limit = 1

    desc = bool(re.search(
        r"\b(maiores|melhores|decrescente|desc|recentes|recente|ultimos|ultimas|ultimo|ultima|"
        r"mais caros|mais caro|mais alto|mais altos)\b",
        question,
    ))
    asc = bool(re.search(
        r"\b(menores|piores|crescente|asc|antigos|antigo|antigas|antiga|primeiros|primeiras|"
        r"primeiro|primeira|mais baratos|mais barato|mais baixo|mais baixos)\b",
        question,
    ))
    order_desc = desc and not asc

    order_by = None
    explicit = re.search(r"\b(?:ordenad[oa]s? por|ordem de|ordenar por|classificad[oa]s? por)\s+([a-z0-9_]+)", question)
    if explicit:
        noun = explicit.group(1)
        for table in [subject] + _related(schema, subject):
            for column in table.columns:
                if noun in forms(column.name):
                    order_by = (table, column)
                    break
            if order_by:
                break
    if order_by is None and measure is not None and (desc or asc or limit):
        order_by = measure
    if order_by is None and group is not None and measure is not None:
        order_by = group
    if order_by is None and (desc or asc):
        date_column = _date_column(subject)
        if date_column is not None and re.search(
            r"\b(recentes|recente|ultimos|ultimas|ultimo|ultima|antigos|antigo|antigas|antiga)\b",
            question,
        ):
            order_by = (subject, date_column)
    return order_by, order_desc, limit


def _extract_having(question: str, group) -> tuple[str, object] | None:
    if group is None:
        return None
    match = re.search(r"\b(?:com|que tem|tendo)\s+(mais|menos)\s+de\s+(\d+)", question)
    if not match:
        return None
    operator = ">" if match.group(1) == "mais" else "<"
    return (operator, int(match.group(2)))


def _extract_distinct(question: str) -> bool:
    return any(word in question.split() for word in lex.DISTINCT_WORDS)


def suggest_questions(schema: Schema, limit: int = 6) -> list[str]:
    """Exemplos de Perguntas que o Motor Offline entende para este schema."""
    tables = list(schema.tables.values())
    single = len(tables) == 1
    suggestions: list[str] = []
    for table in tables[:2]:
        suffix = "" if single else f" de {table.name}"
        suggestions.append("Quantos registros existem?" if single else f"Quantos {table.name} existem?")
        suggestions.append(f"Liste os registros{suffix}")
        text_columns = [
            column
            for column in table.columns
            if column.type == "TEXT" and not column.primary_key and not column.name.lower().endswith("_id")
        ]
        numeric = [
            column
            for column in table.columns
            if column.type in ("INTEGER", "REAL") and _is_measure_column(column)
        ]
        date_column = _date_column(table)
        if numeric:
            suggestions.append(f"Qual o total de {numeric[0].name}?")
            if single:
                suggestions.append(f"Quais os 5 maiores por {numeric[0].name}?")
            else:
                suggestions.append(f"Quais os 5 maiores {table.name} por {numeric[0].name}?")
        if text_columns and numeric:
            suggestions.append(f"Total de {numeric[0].name} por {text_columns[0].name}")
        if date_column:
            suggestions.append(
                "Quantos registros no mes passado?" if single else f"Quantos {table.name} no mes passado?"
            )
            suggestions.append(
                "Qual foi o ultimo registro?"
                if single
                else f"Qual foi o ultimo registro de {table.name}?"
            )
    seen: set[str] = set()
    unique: list[str] = []
    for suggestion in suggestions:
        if suggestion not in seen:
            seen.add(suggestion)
            unique.append(suggestion)
    return unique[:limit]


def _wants_all_columns(question: str) -> bool:
    return bool(
        re.search(r"\b(todos|todas)\s+(os|as)?\s*(campos|colunas|dados|registros|informacoes)\b", question)
    ) or "select *" in question


# ---------------------------------------------------------------------------
# Motor
# ---------------------------------------------------------------------------


class OfflineEngine:
    """Provedor offline: implementa a interface usada pelo pipeline."""

    offline = True

    def __init__(self) -> None:
        self.last_result: OfflineResult | None = None
        self.last_reason = ""

    def test_connection(self) -> None:
        return None

    def generate(self, messages, *, temperature: float = 0.0) -> str:  # pragma: no cover
        raise NotImplementedError("O motor offline nao usa mensagens.")

    def generate_sql(self, question: str, schema: Schema) -> str | None:
        result = self.analyze(question, schema)
        self.last_result = result
        self.last_reason = result.error or ""
        return result.sql

    def analyze(self, question: str, schema: Schema) -> OfflineResult:
        try:
            return self._analyze(question, schema)
        except Exception as exc:  # nunca deixa o app quebrar
            return OfflineResult(
                None,
                {},
                0.0,
                f"Falha interna ao interpretar a pergunta: {exc}",
                self._suggestions(schema),
            )

    def _analyze(self, question: str, schema: Schema) -> OfflineResult:
        q = normalize(question)
        if not q:
            return OfflineResult(None, {}, 0.0, "A pergunta esta vazia.", self._suggestions(schema))

        subject, ambiguous = _find_subject(schema, q)
        if subject is None:
            return OfflineResult(
                None,
                {},
                0.0,
                "Nao identifiquei sobre qual tabela a pergunta e.",
                self._suggestions(schema),
            )
        if ambiguous:
            options = [subject.name, *ambiguous]
            return OfflineResult(
                None,
                {"tabela": subject.name},
                0.4,
                f"A pergunta pode ser sobre mais de uma tabela: {', '.join(options)}. Seja mais especifico.",
                self._suggestions(schema),
                ambiguous=options,
            )

        intent, distinct = self._detect_aggregation(q)
        needs_measure = intent in ("sum", "avg", "min", "max") or bool(
            re.search(r"\b(top|maiores|menores|melhores|piores|mais caros|mais baratos)\b", q)
        )
        measure = _resolve_measure(schema, q, subject) if needs_measure else None
        group = _resolve_group(schema, q, subject)
        if group is None and measure is not None:
            por_match = re.search(r"\bpor\s+([a-z0-9_]+)", q)
            if por_match and por_match.group(1) in lex.MEASURE_WORDS:
                group = (subject, _label_column(subject))

        group_time = None
        if group is None:
            time_match = re.search(r"\bpor\s+(mes|meses|ano|anos|dia|dias)\b", q)
            if time_match:
                unit = time_match.group(1)
                for table in [subject] + _related(schema, subject):
                    date_column = _date_column(table)
                    if date_column is not None:
                        group = (table, date_column)
                        group_time = (
                            "month" if unit.startswith("me") else ("year" if unit.startswith("ano") else "day")
                        )
                        break

        columns = _resolve_columns(schema, q, subject)
        select_all = _wants_all_columns(q)

        filters: list[Filter] = []
        preferred = [item[0] for item in (measure, group) if item is not None]
        date_filter = _extract_date_filter(schema, q, subject, preferred)
        if date_filter:
            filters.append(date_filter)
        for extractor in (
            lambda: _extract_boolean_filter(q, subject),
            lambda: _extract_null_filter(q, subject),
            lambda: _extract_like_filter(q, subject),
            lambda: _extract_text_filter(q, subject),
        ):
            found = extractor()
            if found:
                filters.append(found)
        numeric = _extract_numeric_filter(schema, q, subject, measure)
        if numeric:
            filters.append(numeric)

        order_by, order_desc, limit = _extract_order_limit(schema, q, subject, measure, group)
        having = _extract_having(q, group)

        plan = Plan(
            subject=subject,
            intent=intent,
            measure=measure,
            group=group,
            columns=columns,
            filters=filters,
            order_by=order_by,
            order_desc=order_desc,
            limit=limit,
            distinct=distinct,
            select_all=select_all,
            having=having,
            group_time=group_time,
        )

        sql = self._build(plan, schema)
        if sql is None:
            return OfflineResult(
                None,
                self._understood(plan),
                0.3,
                "Nao consegui montar uma Consulta valida para essa pergunta.",
                self._suggestions(schema),
            )
        return OfflineResult(
            sql,
            self._understood(plan),
            self._confidence(plan),
            explanation=_explain_plan(plan),
        )

    def _detect_aggregation(self, q: str) -> tuple[str, bool]:
        distinct = _extract_distinct(q)
        if re.search(r"\b(quantos|quantas|contagem|numero de)\b", q):
            return "count", distinct
        if re.search(r"\b(media|medias|medio|medios)\b", q):
            return "avg", distinct
        if re.search(r"\b(soma|somatorio|total|faturamento|receita|montante|quanto|quanta)\b", q) or "valor total" in q:
            return "sum", distinct
        if re.search(r"\b(maior|maiores|maximo|maximos|mais caro|mais caros|mais alto|mais altos)\b", q) and not re.search(r"maior(es)? que", q):
            return "max", distinct
        if re.search(r"\b(menor|menores|minimo|minimos|mais barato|mais baratos|mais baixo|mais baixos)\b", q) and not re.search(r"menor(es)? que", q):
            return "min", distinct
        if re.search(r"\b(quais|qual)\b", q) and re.search(r"\b(existe|existem)\b", q):
            distinct = True
        return "list", distinct

    def _understood(self, plan: Plan) -> dict:
        data = {"tabela": plan.subject.name, "intencao": plan.intent}
        if plan.measure:
            data["medida"] = f"{plan.measure[0].name}.{plan.measure[1].name}"
        if plan.group:
            data["agrupar_por"] = f"{plan.group[0].name}.{plan.group[1].name}"
        if plan.filters:
            data["filtros"] = [f"{f.table}.{f.column} {f.operator}" for f in plan.filters]
        if plan.limit:
            data["limite"] = plan.limit
        if plan.distinct:
            data["distintos"] = True
        return data

    def _confidence(self, plan: Plan) -> float:
        score = 0.6
        if plan.intent != "list":
            score += 0.15
        if plan.measure:
            score += 0.1
        if plan.group:
            score += 0.05
        if plan.filters:
            score += 0.05
        return min(score, 0.95)

    # -- construcao ------------------------------------------------------

    def _build(self, plan: Plan, schema: Schema) -> str | None:
        builder = SqlBuilder(schema, plan.subject)

        needed: list[str] = []
        for item in (plan.measure, plan.group, plan.order_by):
            if item is not None:
                needed.append(item[0].name)
        for filter_ in plan.filters:
            needed.append(filter_.table)
        for table, _ in plan.columns:
            needed.append(table.name)
        for name in needed:
            builder.ensure(name)

        where = self._where_sql(plan, builder)

        group_col = plan.group
        measure = plan.measure
        group_expr = self._group_expression(builder, plan)
        measure_expr = builder.col(measure[0].name, measure[1].name) if measure else None

        if plan.limit and group_col is None and measure is not None:
            effective = "list_rank"
        elif group_col is not None and measure is not None and plan.intent in ("list", "max", "min", "sum", "avg"):
            effective = "sum" if plan.intent in ("list", "max", "min") else plan.intent
        else:
            effective = plan.intent

        if effective == "count":
            if plan.distinct:
                if plan.columns:
                    column = plan.columns[0]
                    expression = builder.col(column[0].name, column[1].name)
                elif plan.subject.primary_keys:
                    expression = builder.col(plan.subject.name, plan.subject.primary_keys[0])
                else:
                    expression = None
                aggregate = (
                    f"COUNT(DISTINCT {expression}) AS total" if expression else "COUNT(*) AS total"
                )
            else:
                aggregate = "COUNT(*) AS total"
            if group_expr:
                return self._finish(f"{group_expr} AS grupo, {aggregate}", builder, where, group_expr, plan)
            return self._finish(aggregate, builder, where, None, plan)

        if effective in ("sum", "avg", "min", "max"):
            if measure_expr is None:
                return None
            function = {"sum": "SUM", "avg": "AVG", "min": "MIN", "max": "MAX"}[effective]
            alias = {"sum": "total", "avg": "media", "min": "menor", "max": "maior"}[effective]
            aggregate = f"{function}({measure_expr}) AS {alias}"
            if group_expr:
                order_expr = alias if plan.order_desc else group_expr
                return self._finish(f"{group_expr} AS grupo, {aggregate}", builder, where, group_expr, plan, order_expr)
            return self._finish(aggregate, builder, where, None, plan)

        if effective == "list_rank":
            label = _label_column(plan.subject)
            label_expr = builder.col(plan.subject.name, label.name)
            order_expr = measure_expr or label_expr
            select = f"{label_expr}, {measure_expr}" if measure_expr else label_expr
            return self._finish(select, builder, where, None, plan, order_expr)

        # list
        prefix = "SELECT DISTINCT" if plan.distinct else "SELECT"
        order_expr = builder.col(plan.order_by[0].name, plan.order_by[1].name) if plan.order_by else None
        if plan.select_all:
            select = "*"
        elif plan.columns:
            expressions = [builder.col(table.name, column.name) for table, column in plan.columns]
            expressions = [expression for expression in expressions if expression]
            select = ", ".join(expressions) if expressions else "*"
        elif order_expr:
            select = order_expr
        else:
            label = _label_column(plan.subject)
            select = builder.col(plan.subject.name, label.name) or "*"
        return self._finish(select, builder, where, None, plan, order_expr, prefix)

    def _group_expression(self, builder: SqlBuilder, plan: Plan) -> str | None:
        if plan.group is None:
            return None
        column = builder.col(plan.group[0].name, plan.group[1].name)
        if column is None:
            return None
        if plan.group_time == "month":
            return f"strftime('%Y-%m', {column})"
        if plan.group_time == "year":
            return f"strftime('%Y', {column})"
        if plan.group_time == "day":
            return f"date({column})"
        return column

    def _where_sql(self, plan: Plan, builder: SqlBuilder) -> str:
        conditions: list[str] = []
        for filter_ in plan.filters:
            column = builder.col(filter_.table, filter_.column)
            if column is None:
                continue
            conditions.extend(self._filter_sql(filter_, column))
        return " AND ".join(conditions)

    def _filter_sql(self, filter_: Filter, column: str) -> list[str]:
        if filter_.kind == "numeric":
            if filter_.operator == "between":
                low, high = filter_.value  # type: ignore[misc]
                return [f"{column} BETWEEN {low} AND {high}"]
            return [f"{column} {filter_.operator} {filter_.value}"]
        if filter_.kind == "boolean":
            return [f"{column} = {filter_.value}"]
        if filter_.kind == "null":
            return [f"{column} IS {'NULL' if filter_.operator == 'is_null' else 'NOT NULL'}"]
        if filter_.kind == "like":
            value = str(filter_.value)
            if filter_.operator == "contains":
                return [f"{column} LIKE '%{value}%'"]
            if filter_.operator == "startswith":
                return [f"{column} LIKE '{value}%'"]
            return [f"{column} LIKE '%{value}'"]
        if filter_.kind == "text":
            value = str(filter_.value).replace("'", "''")
            return [f"{column} = '{value}'"]
        if filter_.kind == "date":
            return self._date_sql(filter_, column)
        return []

    def _date_sql(self, filter_: Filter, column: str) -> list[str]:
        mode = filter_.operator
        value = filter_.value
        if mode == "last_month":
            return [f"{column} >= date('now', '-1 month')"]
        if mode == "last_two_months":
            return [f"{column} >= date('now', '-2 month')"]
        if mode == "last_n_months":
            return [f"{column} >= date('now', '-{int(value)} months')"]
        if mode == "last_n_days":
            return [f"{column} >= date('now', '-{int(value)} days')"]
        if mode == "last_n_years":
            return [f"{column} >= date('now', '-{int(value)} years')"]
        if mode == "this_month":
            return [f"{column} >= date('now', 'start of month')"]
        if mode == "last_year":
            return [
                f"{column} >= date('now', 'start of year', '-1 year')",
                f"{column} < date('now', 'start of year')",
            ]
        if mode == "this_year":
            return [f"{column} >= date('now', 'start of year')"]
        if mode == "days_ago":
            return [f"{column} = date('now', '-{int(value)} days')"]
        if mode == "month_name":
            month, year = value  # type: ignore[misc]
            conditions = [f"strftime('%m', {column}) = '{int(month):02d}'"]
            if year:
                conditions.append(f"strftime('%Y', {column}) = '{int(year)}'")
            return conditions
        if mode == "year":
            return [f"strftime('%Y', {column}) = '{int(value)}'"]
        if mode == "quarter":
            index = int(value)
            first = (index - 1) * 3 + 1
            last = first + 2
            return [
                f"strftime('%Y', {column}) = strftime('%Y', 'now')",
                f"CAST(strftime('%m', {column}) AS INTEGER) BETWEEN {first} AND {last}",
            ]
        return []

    def _finish(
        self,
        select: str,
        builder: SqlBuilder,
        where: str,
        group_expr: str | None,
        plan: Plan,
        order_expr: str | None = None,
        prefix: str = "SELECT",
    ) -> str:
        sql = f"{prefix} {select} FROM {builder.from_clause()} {builder.join_clause()}"
        if where:
            sql += f" WHERE {where}"
        if group_expr:
            sql += f" GROUP BY {group_expr}"
        if plan.having and group_expr:
            operator, value = plan.having
            sql += f" HAVING COUNT(*) {operator} {value}"
        if order_expr:
            direction = "DESC" if plan.order_desc else "ASC"
            sql += f" ORDER BY {order_expr} {direction}"
        if plan.limit:
            sql += f" LIMIT {plan.limit}"
        return re.sub(r"\s+", " ", sql).strip().rstrip(";") + ";"

    def _suggestions(self, schema: Schema) -> list[str]:
        return suggest_questions(schema)
