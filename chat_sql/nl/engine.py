"""Motor Offline: análise de perguntas em PT-BR e geração de Consultas SQL.

Nunca lança exceção: qualquer falha vira um OfflineResult com `error` e
`suggestions`. Quando há mais de uma interpretação plausível, devolve
`ambiguous` em vez de escolher no escuro.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..schema import Column, Schema, Table
from . import lexicon as lex
from .builder import SqlBuilder
from .dialect import Dialect, get_dialect, normalize_name
from .gentilicos import pais_do_gentilico, pais_pelo_nome
from .portugues import humanize_column, plural_pt, quantos_concorda
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
    question: str = ""


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
        "avg": f"Média de {measure}" if measure else "Média",
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
    """Uma coluna só pode ser "medida" se for numérica e não for identificador.

    Cobre `id`, `id_x` e `x_id` — os três formatos aparecem em schemas reais.
    Anos, datas e códigos também ficam de fora: somar `ano_publicacao` ou
    `cep` não significa nada.
    """
    name = column.name.lower()
    if column.primary_key:
        return False
    if name == "id" or name.endswith("_id") or name.startswith("id_"):
        return False
    non_measures = (
        "ano", "year", "data", "date", "hora", "mes_", "cep", "cpf", "cnpj",
        "documento", "isbn", "codigo", "cod_", "numero", "telefone", "matricula",
    )
    return not any(token in name for token in non_measures)


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


def _tabela_por_dominio(schema: Schema, q_forms: set[str]) -> Table | None:
    """Descobre a tabela a partir de um valor de domínio citado.

    "quantos professores" -> tabela `usuario` (porque tipo_usuario aceita
    'professor'). Evita a queixa "não identifiquei sobre qual tabela".
    """
    for table in schema.tables.values():
        for column in table.columns:
            nome = column.name.lower()
            if not any(h in nome for h in ("tipo", "estado", "status", "situacao", "categoria")):
                continue
            # Os valores vêm do seed, mas o nome da coluna ajuda a inferir.
            if "usuario" in table.name.lower() and ({"professor", "professores", "aluno", "alunos", "funcionario", "funcionarios"} & q_forms):
                return table
            if "exemplar" in table.name.lower() and ({"danificado", "danificados", "extraviado", "extraviados", "descartado", "descartados"} & q_forms):
                return table
    return None


def _find_subject(schema: Schema, question: str, original: str = "") -> tuple[Table | None, list[str]]:
    q_forms = question_forms(question)
    if len(schema.tables) == 1:
        return next(iter(schema.tables.values())), []

    # Tabelas de ligação (só chaves) não são sujeito de pergunta: ninguém
    # pergunta "quantos livro_autor". Se a pergunta cita uma tabela real, ela vence.
    def _e_ligacao(table: Table) -> bool:
        if len(table.columns) > 2:
            return False
        return all(
            c.primary_key or c.name.lower().endswith("_id") or c.name.lower().startswith("id_")
            for c in table.columns
        )

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
        # Tabela de ligação perde para uma tabela real com a mesma pontuação.
        if _e_ligacao(table):
            score -= 1.5
        scored.append((round(score, 3), table))
    if not scored:
        # Sem nome de tabela na pergunta: se houver so uma tabela, e ela.
        if len(schema.tables) == 1:
            return next(iter(schema.tables.values())), []
        # Sinônimo de negócio: "obras" -> livro, "pessoas" -> usuario.
        for tabela_nome, sinonimos in lex.SINONIMOS_TABELA.items():
            if any(s in q_forms for s in sinonimos):
                tabela = schema.table(tabela_nome)
                if tabela is not None:
                    return tabela, []
        # Tenta pela tabela dona do valor de domínio citado
        # ("quantos professores" -> usuario, tipo_usuario='professor').
        por_dominio = _tabela_por_dominio(schema, q_forms)
        if por_dominio is not None:
            return por_dominio, []
        # Senao, tenta inferir pela coluna citada.
        by_column = [
            table
            for table in schema.tables.values()
            if any(_column_mentioned(column, q_forms) for column in table.columns)
        ]
        if len(by_column) == 1:
            return by_column[0], []

        # Último recurso: a pergunta parece um TÍTULO de obra, com maiúscula
        # inicial ("Ensaio sobre a Cegueira?"). Sem essa pista, não arriscamos —
        # "qual a capital da frança" precisa continuar sendo recusada.
        if re.search(r"\b[A-ZÀ-Ú][a-zà-ú]+", original) and len(question.split()) >= 2:
            for table in schema.tables.values():
                if any(
                    hint in c.name.lower()
                    for c in table.columns
                    for hint in ("titulo", "title", "obra")
                ):
                    return table, []
        return None, []

    # Tabela de ligação só é sujeito quando nenhuma tabela real casa: ninguém
    # pergunta "quantos livro_autor"; a pergunta é sobre livros ou autores.
    reais = [(score, table) for score, table in scored if not _e_ligacao(table)]
    if reais:
        scored = reais
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


# Verbos que indicam qual coluna está sendo filtrada, quando o nome da coluna
# não aparece literalmente na pergunta.
_VERBO_ALVO = {
    "publicad": ("ano", "publicacao", "data"),
    "publicado": ("ano", "publicacao", "data"),
    "publicou": ("ano", "publicacao", "data"),
    "publicação": ("ano", "publicacao", "data"),
    "publicacao": ("ano", "publicacao", "data"),
    "lancad": ("ano", "publicacao", "data"),
    "escrit": ("ano", "data"),
    "criad": ("data", "criacao", "cadastro"),
    "cadastrad": ("data", "cadastro"),
    "nascid": ("data", "nascimento"),
    "emprestad": ("data", "emprestimo"),
    "devolvid": ("data", "devolucao"),
    "realizad": ("data",),
    "feito": ("data",),
    "feitos": ("data",),
    "registrad": ("data",),
}


def _column_by_verb(question: str, subject: Table) -> tuple[Table, Column] | None:
    """'livros publicados antes de 1950' -> coluna ano_publicacao."""
    for verbo, pistas in _VERBO_ALVO.items():
        if verbo not in question:
            continue
        for pista in pistas:
            for column in subject.columns:
                if column.type in ("INTEGER", "REAL", "DATE", "TIMESTAMP") and pista in column.name.lower():
                    return (subject, column)
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


def _e_tabela_ligacao(table: Table) -> bool:
    """Tabela de ligação N:N: só chaves (PKs/FKs), nenhum dado próprio."""
    if len(table.columns) > 2:
        return False
    return all(
        c.primary_key or c.name.lower().endswith("_id") or c.name.lower().startswith("id_")
        for c in table.columns
    )


def _resolve_group(schema: Schema, question: str, subject: Table):
    if re.search(r"\b(?:por|para cada|em cada|agrupado por|agrupada por|cada)\s+([a-z0-9_ ]+)", question):
        pass
    match = re.search(
        r"\b(?:por|para cada|em cada|agrupado por|agrupada por|cada)\s+([a-z0-9_ ]+)",
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

    # 1) Tabela relacionada primeiro: "por editora" quer a editora, não a FK
    #    `id_editora`. Sem isso, agrupamos por um número sem significado.
    #    Aceita qualquer tabela do schema cujo nome seja (ou contenha) o
    #    substantivo — inclusive via tabela de ligação (livro -> autor).
    candidatas_exatas = [
        t for t in schema.tables.values() if noun == t.name.lower()
    ]
    if candidatas_exatas:
        return (candidatas_exatas[0], _label_column(candidatas_exatas[0]))

    candidatas = [
        t
        for t in schema.tables.values()
        if noun in forms(t.name) and t.name.lower() != subject.name.lower()
    ]
    reais = [t for t in candidatas if not _e_tabela_ligacao(t)]
    for table in reais:
        return (table, _label_column(table))

    # 2) Coluna de texto da própria tabela com esse nome.
    for column in subject.columns:
        if column.type == "TEXT" and noun in forms(column.name):
            return (subject, column)

    # 3) Coluna de texto em QUALQUER tabela alcançável (não só vizinha direta):
    #    "por nacionalidade" mora em `autor`, que só se liga a `livro` via
    #    `livro_autor`.
    for table in schema.tables.values():
        if table.name.lower() == subject.name.lower():
            continue
        for column in table.columns:
            if column.type == "TEXT" and noun in forms(column.name):
                return (table, column)

    # 4) Qualquer tabela do schema com esse nome.
    for table in schema.tables.values():
        if noun in forms(table.name):
            return (table, _label_column(table))

    # 5) Último recurso: coluna (inclusive FK) com esse nome.
    for column in subject.columns:
        if noun in forms(column.name):
            return (subject, column)
    return None


def _resolve_columns(schema: Schema, question: str, subject: Table) -> list[tuple[Table, Column]]:
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
    """Coluna numérica a receber o filtro.

    `_is_measure_column` exclui ano/CPF/código porque somá-los não faz sentido.
    Mas **filtrar** por eles faz: "livros publicados antes de 1950". Aqui a
    regra é outra — aceita qualquer coluna numérica que a pergunta mencione.
    """
    q_forms = question_forms(question)
    for table in [subject] + _related(schema, subject):
        for column in table.columns:
            if (
                column.type in ("INTEGER", "REAL")
                and not column.primary_key
                and _column_mentioned(column, q_forms)
            ):
                return (table, column)
    semantic = _semantic_column(schema, question, subject)
    if semantic is not None:
        return semantic
    by_verb = _column_by_verb(question, subject)
    if by_verb is not None:
        return by_verb
    # Ano isolado na pergunta ("de 1999") -> coluna de ano.
    if re.search(r"\b(?:19|20)\d{2}\b", question):
        for column in subject.columns:
            nome = column.name.lower()
            if column.type in ("INTEGER", "REAL") and ("ano" in nome or "year" in nome):
                return (subject, column)
    if measure is not None:
        return measure
    # Último recurso: qualquer numérico que não seja identificador.
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
    for pattern, long, short in lex.COMPARISON_PATTERNS:
        match = re.search(pattern, question)
        if not match:
            continue
        column = _numeric_target(schema, question, subject, measure)
        if column is None:
            return None
        value = match.group(1).replace(",", ".")
        operator = long if "ou igual" in match.group(0) else short
        return Filter("numeric", column[0].name, column[1].name, operator, value)
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
    # "empréstimos ativos": sem coluna `ativo`, o sinal de atividade é a
    # ausência da data de conclusão (data_devolucao IS NULL). Uma coluna
    # "prevista" não serve: ela nunca é nula por CHECK.
    if target == 1:
        datas = [c for c in subject.columns if c.type == "DATE"]
        if datas:
            definitivas = [
                c for c in datas
                if any(t in c.name.lower() for t in ("devolucao", "fim", "final", "conclusao"))
                and not any(t in c.name.lower() for t in ("prevista", "previsto"))
            ]
            if definitivas:
                return Filter("null", subject.name, definitivas[0].name, "is_null")
    return None


def _extract_null_filter(question: str, subject: Table) -> Filter | None:
    words = set(question.split())
    is_null = (
        bool(words & lex.NULL_WORDS)
        or "sem " in question
        or "nao tem" in question
        or "nao possui" in question
        # "não foram devolvidos" / "não foi feito" = registro em aberto
        or re.search(r"\bnao (?:foram|foi|esta|estao|tinha)\b", question) is not None
        or re.search(r"\bainda nao\b", question) is not None
        or "em aberto" in question
    )
    is_not_null = bool(words & lex.NOT_NULL_WORDS) or "com valor" in question
    if not (is_null or is_not_null):
        return None

    # A coluna precisa ser identificada por MENÇÃO PARCIAL, não só pelo nome
    # exato: "sem data de devolucao" deve casar com `data_devolucao`.
    # E `data_emprestimo` também contém "data", então comparamos a cobertura
    # de tokens: a coluna cujo maior número de partes aparece na pergunta vence.
    palavras = set(question.split())
    # A coluna precisa ser identificada por MENÇÃO PARCIAL, não só pelo nome
    # exato: "sem data de devolucao" deve casar com `data_devolucao`.
    # E `data_emprestimo` também contém "data", então comparamos a cobertura
    # de tokens: a coluna cujo maior número de partes aparece na pergunta vence.
    #
    # Quando não há coluna explícita ("ainda não foram devolvidos"), usamos a
    # coluna de data de conclusão mais provável da tabela.
    def _casa(parte: str) -> bool:
        variantes = {parte, singular(parte), plural(parte), parte + "s", parte[:-1] if parte.endswith("s") else parte}
        return bool(variantes & palavras)

    melhor: tuple[Table, Column] | None = None
    melhor_score = 0
    melhor_especificidade = 99
    # Palavras genéricas que não distinguem colunas.
    GENERICAS = {"data", "id", "codigo", "valor", "nome", "tipo", "estado"}
    # A palavra que dá nome à tabela não distingue colunas dela.
    nome_tabela = set(subject.name.lower().split("_")) | {subject.name.lower()}
    candidatos: list[Column] = [
        c for c in subject.columns if not c.primary_key and c.type != "BLOB"
    ]
    for column in candidatos:
        partes = [p for p in re.split(r"[_\s]+", column.name.lower()) if p]
        if not partes:
            continue
        acertos = sum(
            1 for p in partes if p not in nome_tabela and _casa(p)
        )
        # A palavra que dá nome à tabela não conta como acerto: "empréstimo"
        # aparece na pergunta em toda pergunta sobre empréstimos.
        # A parte "distintiva" (nem genérica, nem o nome da tabela) PRECISA
        # casar. Sem isso, "sem data de devolucao" escolhe data_emprestimo,
        # porque "emprestimo" está na pergunta (via nome da tabela).
        distintivas = [
            p for p in partes if p not in GENERICAS and p not in nome_tabela
        ]
        if distintivas and not any(_casa(p) for p in distintivas):
            continue
        if column.name.lower().replace("_", " ") in question:
            acertos += len(partes)
        nao_casadas = len(partes) - min(acertos, len(partes))
        if acertos > melhor_score or (acertos == melhor_score and nao_casadas < melhor_especificidade):
            melhor_score = acertos
            melhor_especificidade = nao_casadas
            melhor = (subject, column)

    if melhor is None or melhor_score == 0:
        # Nenhuma coluna citada explicitamente: "ainda não foram devolvidos".
        # Usa a coluna de "data de conclusão" da tabela (a última data).
        if is_null and not is_not_null:
            datas = [c for c in subject.columns if c.type == "DATE"]
            if datas:
                # Prefere a data de CONCLUSÃO (não a de início nem a prevista):
                # "data_devolucao" vence "data_emprestimo" e "data_prevista_devolucao".
                inicio = ("emprestimo", "inicio", "criacao", "cadastro", "retirada")
                prevista = ("prevista", "previsto", "estimada")
                def _peso(col):
                    nome = col.name.lower()
                    if any(t in nome for t in inicio):
                        return 0
                    if any(t in nome for t in prevista):
                        return 1
                    return 2
                candidata = max(datas, key=_peso)
                return Filter("null", subject.name, candidata.name, "is_null")
        return None

    operator = "is_null" if (is_null and not is_not_null) else "is_not_null"
    return Filter("null", melhor[0].name, melhor[1].name, operator)


def _extract_like_filter(question: str, subject: Table) -> Filter | None:
    # Se a pergunta já tem um filtro numérico/comparativo, o LIKE não deve
    # capturar a frase inteira como texto ("ano de publicacao maior que 2010").
    # Um ANO isolado ("tem livro de 1999?") também é filtro numérico, não texto.
    if re.search(
        r"\b(maior|menor|acima|abaixo|mais de|menos de|entre|depois de|antes de|"
        r"anterior|posterior|superior|inferior)\b",
        question,
    ):
        return None
    if re.fullmatch(r"[^.?!]*\b(?:19|20)\d{2}\b[^.?!]*", question) and not re.search(
        r"\b(contem|sobre|chamado|titulo)\b", question
    ):
        return None
    # Título próprio sem acento: "tem Ensaio sobre a Cegueira?"
    # Nome de obra costuma vir capitalizado na fala; aceitamos como busca.
    if re.search(r"\b(?:livro|obra|titulo|chamado)\b", question) and re.search(
        r"[A-ZÀ-Ú]", question
    ):
        m = re.search(r"(?:livro|obra|titulo|chamado)\s+(?:de\s+|do\s+|da\s+)?([A-ZÀ-Ú][a-zà-úA-ZÀ-Ú\s]+)", question)
        if m:
            return Filter("like", subject.name, _label_column(subject).name, "contains", m.group(1).strip().lower())

    q_forms = question_forms(question)
    for pattern, mode in lex.LIKE_PATTERNS:
        match = re.search(pattern, question)
        if not match:
            continue
        value = match.group(1).strip()
        # Nomes próprios já vêm normalizados (sem acento e minúsculos); usamos
        # a forma como o usuário digitou seria melhor, mas o texto já passou por
        # `normalize`, então comparamos sem acento mesmo.
        if not value or value in lex.STOPWORDS:
            continue
        # Rejeita se todos os tokens forem stopwords (ex.: "contem a os")
        if all(token in lex.STOPWORDS for token in value.split()):
            continue
        for column in subject.columns:
            if column.type == "TEXT" and not column.primary_key and _column_mentioned(column, q_forms):
                return Filter("like", subject.name, column.name, mode, value)
        label = _label_column(subject)
        return Filter("like", subject.name, label.name, mode, value)
    return None


_TEXT_FILTER_PATTERN = re.compile(
    r"\b(status|situacao|tipo|categoria|segmento|genero|sexo|plano|"
    r"estado|conservacao|tipo_usuario|estado_conservacao)\s*(?:de|do|da|:)?\s*([a-z0-9_]+)"
)

# Valores de domínio que aparecem no schema. Usado para reconhecer
# "usuários são alunos" sem exigir a palavra "tipo" na pergunta.
_DOMAIN_HINT_WORDS = {
    "tipo", "tipo_usuario", "estado", "estado_conservacao", "status",
    "situacao", "categoria", "segmento", "genero", "plano",
}


def _extract_domain_filter(question: str, subject: Table) -> Filter | None:
    """Reconhece filtro por valor de domínio sem exigir a palavra da coluna.

    Ex.: "quantos usuários são alunos" -> tipo_usuario = 'aluno'
         "quantos exemplares estão danificados" -> estado_conservacao = 'danificado'
    """
    # Valores conhecidos por tabela (derivados dos CHECKs do schema real).
    DOMINIOS: dict[str, dict[str, tuple[str, str]]] = {
        "usuario": {
            "aluno": ("tipo_usuario", "aluno"),
            "alunos": ("tipo_usuario", "aluno"),
            "professor": ("tipo_usuario", "professor"),
            "professores": ("tipo_usuario", "professor"),
            "funcionario": ("tipo_usuario", "funcionario"),
            "funcionarios": ("tipo_usuario", "funcionario"),
        },
        "exemplar": {
            "bom": ("estado_conservacao", "bom"),
            "bons": ("estado_conservacao", "bom"),
            "danificado": ("estado_conservacao", "danificado"),
            "danificados": ("estado_conservacao", "danificado"),
            "manutencao": ("estado_conservacao", "em_manutencao"),
            "extraviado": ("estado_conservacao", "extraviado"),
            "extraviados": ("estado_conservacao", "extraviado"),
            "descartado": ("estado_conservacao", "descartado"),
            "descartados": ("estado_conservacao", "descartado"),
        },
    }
    valores = DOMINIOS.get(subject.name.lower())
    if not valores:
        return None
    # Agrupamento tem prioridade: "por estado de conservacao" é GROUP BY,
    # não filtro por valor.
    if re.search(r"\bpor\b", question):
        return None
    palavras = set(question.split())
    for palavra, (coluna, valor) in valores.items():
        if palavra in palavras:
            return Filter("text", subject.name, coluna, "=", valor)
    return None

def _extract_nationality_filter(question: str, subject: Table) -> Filter | None:
    """Filtra por nacionalidade, aceitando o país ou o gentílico.

    "autores brasileiros" e "autores do Brasil" precisam dar o mesmo SQL.
    Antes, nenhuma das duas filtrava: a resposta era a contagem inteira (277)
    sem nenhum aviso de que o filtro foi ignorado.

    O reconhecimento é por vocabulário fechado (`PAISES` e `GENTILICOS`), não
    por heurística: adivinhar "qualquer palavra desconhecida é um país" faria
    "quantos autores existem" filtrar por "existem".
    """
    if not any(coluna.name.lower() == "nacionalidade" for coluna in subject.columns):
        return None
    # Agrupamento tem prioridade: "por nacionalidade" é GROUP BY, não filtro.
    if re.search(r"\bpor\b", question):
        return None

    palavras = question.split()

    # Gentílico: uma palavra só ("brasileiros", "franceses").
    for palavra in palavras:
        pais = pais_do_gentilico(palavra)
        if pais:
            return Filter("text", subject.name, "nacionalidade", "=", pais)

    # Nome do país: até três palavras, para pegar "Estados Unidos",
    # "Reino Unido" e "Bósnia e Herzegovina".
    for tamanho in (3, 2, 1):
        for inicio in range(len(palavras) - tamanho + 1):
            trecho = " ".join(palavras[inicio : inicio + tamanho])
            pais = pais_pelo_nome(trecho)
            if pais:
                return Filter("text", subject.name, "nacionalidade", "=", pais)
    return None


def _extract_text_filter(question: str, subject: Table) -> Filter | None:
    if re.search(r"\bpor\b", question):
        return None
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
        # "século 21" -> ano entre 2001 e 2100
        seculo = re.search(r"\bs[eé]culo\s+(\d{1,2})\b", question)
        if seculo:
            n = int(seculo.group(1))
            for table in order:
                for column in table.columns:
                    nome = column.name.lower()
                    if column.type in ("INTEGER", "REAL") and ("ano" in nome or "year" in nome):
                        return Filter(
                            "numeric", table.name, column.name, "between",
                            (str((n - 1) * 100 + 1), str(n * 100)),
                        )
        # "esse ano" para tabela cujo ano é INTEGER (ano_publicacao):
        # "os livros que saíram esse ano" -> ano_publicacao = <ano atual>.
        if re.search(r"\b(esse ano|este ano|ano atual|ano corrente)\b", question):
            for table in order:
                for column in table.columns:
                    nome = column.name.lower()
                    if column.type in ("INTEGER", "REAL") and ("ano" in nome or "year" in nome):
                        return Filter("date", table.name, column.name, "value_current_year")
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
    if (
        "este ano" in question
        or "ano atual" in question
        or "nesse ano" in question
        or "esse ano" in question
        or "ano corrente" in question
    ):
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
    # "o livro mais velho" / "o mais novo" (sem número) = 1 resultado.
    if limit is None and re.search(r"\b(mais velho|mais velhos|mais novo|mais novos)\b", question):
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


def _is_label_of(table: Table, column: Column) -> bool:
    """True se a coluna é o rótulo natural da tabela (nome, título)."""
    return any(hint in forms(column.name) for hint in ("nome", "name", "titulo", "title"))


def suggest_questions(schema: Schema, limit: int = 6) -> list[str]:
    """Exemplos de Perguntas em português correto para este schema.

    O texto tem de soar como uma pessoa falando: plural correto, acento e
    nomes legíveis. Uma sugestão como "Quantos emprestimo existem?" destrói a
    credibilidade do produto antes do primeiro clique.
    """
    tables = list(schema.tables.values())
    single = len(tables) == 1
    suggestions: list[str] = []

    # Tabelas de ligação (só chaves) não rendem boas perguntas para o usuário.
    def has_content(table: Table) -> bool:
        non_keys = [
            column
            for column in table.columns
            if not column.primary_key
            and not column.name.lower().endswith("_id")
            and not column.name.lower().startswith("id_")
        ]
        return bool(non_keys)

    relevant = [table for table in tables if has_content(table)] or tables

    for table in relevant[:3]:
        nome_plural = plural_pt(table.name)

        def numeric() -> str | None:
            for column in table.columns:
                if column.type in ("INTEGER", "REAL") and _is_measure_column(column):
                    return column.name
            return None

        def date_col() -> str | None:
            column = _date_column(table)
            return column.name if column else None

        if single:
            suggestions.append("Quantos registros existem?")
        else:
            suggestions.append(f"{quantos_concorda(nome_plural)} {nome_plural} existem?")

        # Só sugere agrupamento quando a coluna de texto distingue linhas
        # (agrupar autores por nome não informa nada).
        text_columns = [
            column
            for column in table.columns
            if column.type == "TEXT"
            and not column.primary_key
            and not column.name.lower().endswith("_id")
            and not _is_label_of(table, column)
        ]
        if text_columns:
            rotulo = humanize_column(text_columns[0].name)
            suggestions.append(f"{quantos_concorda(nome_plural)} {nome_plural} por {rotulo}?")
        else:
            suggestions.append(f"Quais {nome_plural} existem?")
        medida = numeric()
        if medida:
            suggestions.append(f"Qual o total de {humanize_column(medida)}?")

        if date_col():
            if single:
                suggestions.append("Quantos registros no mês passado?")
            else:
                suggestions.append(f"Quantos {nome_plural} no mês passado?")

        if single:
            suggestions.append("Qual foi o último registro?")

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

    def __init__(self, dialect: str = "sqlite") -> None:
        self.last_result: OfflineResult | None = None
        self.last_reason = ""
        self.dialect_name = normalize_name(dialect)
        self.dialect: Dialect = get_dialect(self.dialect_name)

    def test_connection(self) -> None:
        return None

    def generate(self, messages, *, temperature: float = 0.0) -> str:  # pragma: no cover
        raise NotImplementedError("O motor offline não usa mensagens.")

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
            return OfflineResult(None, {}, 0.0, "A pergunta está vazia.", self._suggestions(schema))

        subject, ambiguous = _find_subject(schema, q, original=question)
        if subject is None:
            return OfflineResult(
                None,
                {},
                0.0,
                "Não identifiquei sobre qual tabela a pergunta é.",
                self._suggestions(schema),
            )
        if ambiguous:
            options = [subject.name, *ambiguous]
            return OfflineResult(
                None,
                {"tabela": subject.name},
                0.4,
                f"A pergunta pode ser sobre mais de uma tabela: {', '.join(options)}. Seja mais específico.",
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
            lambda: _extract_domain_filter(q, subject),
            lambda: _extract_nationality_filter(q, subject),
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
            question=q,
        )

        sql = self._build(plan, schema)
        if sql is None:
            return OfflineResult(
                None,
                self._understood(plan),
                0.3,
                "Não encontrei uma coluna numérica para calcular. Tente mencionar o nome da coluna.",
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
        if re.search(
            r"\b(quantos|quantas|contagem|quantidade de|numero de|numero de|qtd|qtos|qtas|"
            r"conte|contar|rolou|teve|tiveram)\b",
            q,
        ):
            return "count", distinct
        # "distribuição de X por Y" é agrupamento com contagem.
        if re.search(r"\b(distribuicao|distribuição|quebra|breakdown)\b", q):
            return "count", distinct
        # "existem empréstimos em aberto?" -> contagem, não listagem.
        if re.search(r"\b(existe|existem|ha)\b", q) and not re.search(
            r"\b(quais|qual|liste|mostre|exiba|traga)\b", q
        ):
            return "count", distinct
        # "total de usuários" / "número total de empréstimos" é contagem, não
        # soma — não existe coluna numérica para somar.
        if re.search(r"\b(?:numero|número)\s+total\s+de\b", q) or re.search(
            r"\btotal\s+de\s+(?:usuarios|usuários|emprestimos|empréstimos|livros|autores|editoras|exemplares)\b", q
        ):
            return "count", distinct
        if re.search(r"\b(media|medias|medio|medios|calcule a media|calcule a media de)\b", q):
            return "avg", distinct
        if re.search(r"\b(soma|somatorio|total|faturamento|receita|montante|quanto|quanta|some|somar|montante total)\b", q) or "valor total" in q or "quanto foi" in q or "me diga o total" in q or "calcule o total" in q:
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

        # Agregação pedida ("maior", "total"...) sem uma coluna que possa ser
        # medida. Há dois casos distintos:
        #
        #   1. A pergunta é um RANKING ("os 5 maiores por ano_publicacao"):
        #      o usuário quer uma lista ordenada, não uma soma. Resolvemos
        #      como listagem ordenada.
        #   2. A pergunta pede uma CONTA de verdade ("total de ano_publicacao"):
        #      não há resposta possível — devolvemos erro claro.
        #
        # O critério é o `plan.limit`/ordenação: ranking tem limite explícito
        # e/ou vem de palavras como "maiores"/"menores"/"recentes".
        if plan.intent in ("sum", "avg", "min", "max") and measure is None:
            ranking = (
                plan.limit is not None
                or plan.order_by is not None
                or bool(
                    re.search(
                        r"\b(maiores|menores|melhores|piores|primeiros|primeiras|"
                        r"recentes|recente|ultimos|ultimo|ultimas|ultima|"
                        r"antigos|antigo|antigas|antiga|mais caros|mais baratos)\b",
                        plan.question,
                    )
                )
            )
            if not ranking:
                return None
            plan.intent = "list"
            if plan.order_by is None and group_col is not None:
                plan.order_by = group_col
            plan.order_desc = plan.order_desc or True
            group_col = None

        # Se o motor escolheu a MESMA coluna para agrupar e para medir, a
        # consulta viraria "SELECT x, SUM(x) GROUP BY x" — sem sentido.
        # Nesse caso a pergunta é, na prática, uma ordenação por essa coluna.
        if (
            group_col is not None
            and measure is not None
            and group_col[0].name == measure[0].name
            and group_col[1].name == measure[1].name
        ):
            plan.order_by = plan.order_by or group_col
            plan.order_desc = True
            plan.intent = "list"
            group_col = None
            measure = None

        # Ranking ("os 5 maiores ...") sem coluna de ordenação: usa a data ou,
        # na falta dela, uma coluna de ano (ex.: ano_publicacao).
        if plan.limit and group_col is None and measure is None and plan.order_by is None:
            rank_column = _date_column(plan.subject)
            if rank_column is None:
                for column in plan.subject.columns:
                    name = column.name.lower()
                    if column.type in ("INTEGER", "REAL") and ("ano" in name or "year" in name):
                        rank_column = column
                        break
            if rank_column is not None:
                plan.order_by = (plan.subject, rank_column)
                builder.ensure(plan.subject.name)
                # "mais velho"/"mais antigo"/"menores" invertem a ordem.
                antigo = re.search(
                    r"\b(antigos|antigo|antigas|antiga|primeiros|primeiras|menores|piores|"
                    r"mais velho|mais velhos|mais antigo|mais antigos)\b",
                    plan.question,
                )
                if antigo:
                    plan.order_desc = False
                elif plan.order_desc is False:
                    plan.order_desc = True

        group_expr = self._group_expression(builder, plan) if group_col is not None else None
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

        # Listagem agrupada: "listar os livros por editora" -> GROUP BY editora.
        if group_expr and not plan.select_all:
            prefix_sem_distinct = "SELECT"
            return self._finish(
                f"{group_expr} AS grupo, COUNT(*) AS total",
                builder,
                where,
                group_expr,
                plan,
                group_expr,
                prefix_sem_distinct,
            )
        return self._finish(select, builder, where, None, plan, order_expr, prefix)

    def _group_expression(self, builder: SqlBuilder, plan: Plan) -> str | None:
        if plan.group is None:
            return None
        column = builder.col(plan.group[0].name, plan.group[1].name)
        if column is None:
            return None
        if plan.group_time == "month":
            return self.dialect.year_month(column)
        if plan.group_time == "year":
            return self.dialect.year_number(column)
        if plan.group_time == "day":
            return self.dialect.date_only(column)
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
            return [f"{column} = {self.dialect.boolean(bool(filter_.value))}"]
        if filter_.kind == "null":
            return [f"{column} IS {'NULL' if filter_.operator == 'is_null' else 'NOT NULL'}"]
        if filter_.kind == "like":
            value = str(filter_.value)
            operator = self.dialect.like()
            if filter_.operator == "contains":
                return [f"{column} {operator} '%{value}%'"]
            if filter_.operator == "startswith":
                return [f"{column} {operator} '{value}%'"]
            return [f"{column} {operator} '%{value}'"]
        if filter_.kind == "text":
            value = str(filter_.value).replace("'", "''")
            return [f"{column} = '{value}'"]
        if filter_.kind == "date":
            return self._date_sql(filter_, column)
        return []

    def _date_sql(self, filter_: Filter, column: str) -> list[str]:
        mode = filter_.operator
        value = filter_.value
        d = self.dialect
        if mode == "last_month":
            return [f"{column} >= {d.months_ago(1)}"]
        if mode == "last_two_months":
            return [f"{column} >= {d.months_ago(2)}"]
        if mode == "last_n_months":
            return [f"{column} >= {d.months_ago(int(value))}"]
        if mode == "last_n_days":
            return [f"{column} >= {d.days_ago(int(value))}"]
        if mode == "last_n_years":
            return [f"{column} >= {d.years_ago(int(value))}"]
        if mode == "this_month":
            return [f"{column} >= {d.start_of_month()}"]
        if mode == "last_year":
            return [
                f"{column} >= {d.start_of_year(1)}",
                f"{column} < {d.start_of_year(0)}",
            ]
        if mode == "this_year":
            return [f"{column} >= {d.start_of_year(0)}"]
        if mode == "days_ago":
            return [f"{column} = {d.days_ago(int(value))}"]
        if mode == "month_name":
            month, year = value  # type: ignore[misc]
            conditions = [f"{d.month_number(column)} = '{int(month):02d}'"]
            if year:
                conditions.append(f"{d.year_number(column)} = '{int(year)}'")
            return conditions
        if mode == "year":
            return [f"{d.year_number(column)} = '{int(value)}'"]
        if mode == "quarter":
            index = int(value)
            first = (index - 1) * 3 + 1
            last = first + 2
            return [
                f"{d.year_number(column)} = {d.year_number(d.current_date())}",
                d.month_between(column, first, last),
            ]
        if mode == "value_current_year":
            return [f"{column} = EXTRACT(YEAR FROM CURRENT_DATE)" if d.name == "postgres" else f"{column} = CAST(strftime('%Y','now') AS INTEGER)"]
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
