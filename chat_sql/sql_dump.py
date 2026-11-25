"""Importação de arquivo `.sql` (dump).

Um dump contém `CREATE TABLE` e, normalmente, `INSERT INTO`. O app já aceita
colar esse script na aba Dados; este módulo permite enviar o **arquivo**, que é
o caso comum ao migrar de um sistema antigo.

O caminho de execução é o mesmo do Script SQL: `InMemoryDatabase(schema)` sem
dados de exemplo, porque os `INSERT` já estão no script.

## Por que existe conversão

O banco de execução é SQLite em memória, mas os dumps reais quase nunca são
SQLite. Um dump padrão do MySQL (`ENGINE=InnoDB`, `AUTO_INCREMENT`, `int(11)`,
`KEY nome (col)`) não roda em SQLite de forma alguma. Baixar o arquivo e falhar
com "syntax error" seria inútil para quem está migrando um sistema antigo.

Então o dump é convertido para SQLite **antes** de executar:

1. `sqlglot` transpila MySQL -> SQLite (se o dialeto de origem for MySQL);
2. uma normalização remove o que o SQLite não aceita (`INTEGER(11)`,
   `VARCHAR(120)`, `INDEX nome (col)` inline);
3. se qualquer etapa falhar, o texto original é devolvido intacto — nunca
   pioramos um dump que já funcionava.

`prepare()` continua devolvendo o texto a ser executado, então o resto do app
não precisa saber que houve conversão.
"""

from __future__ import annotations

import logging
import re

import sqlglot
from sqlglot.errors import SqlglotError

# O sqlglot avisa "Unsupported property engineproperty" ao ler
# `ENGINE=InnoDB` / `DEFAULT CHARSET=...`. É ruído esperado: a propriedade é
# ignorada de propósito, e o aviso apareceria no terminal a cada importação.
# Erros de verdade continuam chegando como exceção (ParseError).
logging.getLogger("sqlglot").setLevel(logging.ERROR)


class DumpError(Exception):
    """Arquivo que não parece um dump SQL válido."""


_ENCODINGS = ("utf-8-sig", "utf-8", "latin-1", "cp1252")

_CREATE_RE = re.compile(r"\bcreate\s+table\b", re.IGNORECASE)
_INSERT_RE = re.compile(r"\binsert\s+into\b", re.IGNORECASE)

# Marcas de que o dump veio do MySQL/MariaDB.
_MYSQL_RE = re.compile(
    r"engine\s*=\s*innodb|\bauto_increment\b|/\*!\d{5}\s|`[^`]+`",
    re.IGNORECASE,
)


def decode_dump(content: bytes) -> str:
    """Decodifica o arquivo tentando UTF-8 e, se falhar, latin-1.

    Dumps antigos (MySQL, Access, sistemas legados) quase sempre vêm em
    latin-1/cp1252. Ordem: UTF-8 com BOM, UTF-8, latin-1, cp1252.
    """
    if not content:
        raise DumpError("O arquivo está vazio.")

    for encoding in _ENCODINGS:
        try:
            texto = content.decode(encoding)
        except UnicodeDecodeError:
            continue
        # latin-1 decodifica qualquer byte; se chegamos nele, é o resultado.
        return texto

    return content.decode("utf-8", errors="replace")


def looks_like_dump(text: str) -> bool:
    """True se o texto tem `CREATE TABLE` e pelo menos um `INSERT INTO`."""
    if not text:
        return False
    return bool(_CREATE_RE.search(text)) and bool(_INSERT_RE.search(text))


def has_create(text: str) -> bool:
    """True se há pelo menos um `CREATE TABLE` (dump só de estrutura)."""
    return bool(text) and bool(_CREATE_RE.search(text))


def is_mysql_dump(text: str) -> bool:
    """True quando o texto tem marcas típicas de dump MySQL/MariaDB."""
    return bool(text) and bool(_MYSQL_RE.search(text))


# Tamanho/precisão de tipo: INTEGER(11), VARCHAR(120), DECIMAL(10,2).
# O SQLite aceita só o nome base — e `INTEGER(11) ... AUTOINCREMENT` é erro.
_TYPE_SIZE_RE = re.compile(
    r"\b(?:"
    r"INTEGER|INT|BIGINT|SMALLINT|TINYINT|MEDIUMINT"
    r"|VARCHAR|CHAR|NVARCHAR|NCHAR|TEXT"
    r"|DECIMAL|NUMERIC|NUMBER|REAL|DOUBLE(?:\s+PRECISION)?"
    r")\s*\(\s*\d+\s*(?:,\s*\d+\s*)?\)",
    re.IGNORECASE,
)

# Cláusula de índice inline que o sqlglot deixa no CREATE TABLE:
# `, INDEX "idx" ("col")` e `, KEY "idx" ("col")`.
_INLINE_INDEX_RE = re.compile(
    r",\s*(?:INDEX|KEY)\s+(?:\"[^\"]*\"|`[^`]*`|[\w$]+)\s*\([^)]*\)",
    re.IGNORECASE,
)


def _simplify_types(sql: str) -> str:
    """Troca tipos com tamanho pelo tipo base aceito pelo SQLite."""

    def troca(match: re.Match) -> str:
        base = match.group(0).split("(")[0].strip().upper()
        if base in {"VARCHAR", "CHAR", "NVARCHAR", "NCHAR", "TEXT"}:
            return "TEXT"
        if base in {"DECIMAL", "NUMERIC", "NUMBER", "REAL"} or base.startswith("DOUBLE"):
            return "REAL"
        return "INTEGER"

    return _TYPE_SIZE_RE.sub(troca, sql)


def _drop_inline_indexes(sql: str) -> str:
    return _INLINE_INDEX_RE.sub("", sql)


def _to_sqlite(text: str) -> str:
    """Converte um dump MySQL em script que o SQLite executa.

    Levanta DumpError se a conversão não produzir nada utilizável.
    """
    try:
        statements = sqlglot.transpile(text, read="mysql", write="sqlite")
    except (SqlglotError, ValueError) as exc:
        raise DumpError(f"Não consegui interpretar o dump MySQL: {exc}") from exc

    if not statements:
        raise DumpError("O dump não contém nenhuma instrução reconhecível.")

    partes = []
    for statement in statements:
        if not statement or not statement.strip():
            continue
        sql = _drop_inline_indexes(_simplify_types(statement)).strip()
        if sql:
            partes.append(sql)

    if not partes:
        raise DumpError("O dump não contém nenhuma instrução reconhecível.")

    return ";\n".join(partes) + ";"


def normalize_for_sqlite(text: str) -> str:
    """Prepara o texto para executar no SQLite, preservando-o se não for MySQL.

    - SQLite puro (ou desconhecido): devolve **o texto original**, sem tocar.
    - MySQL: transpila e simplifica.
    - Se a conversão falhar: devolve o original, para o erro vir da execução
      com a mensagem real do SQLite — mais útil que uma mensagem de conversão.
    """
    if not is_mysql_dump(text):
        return text
    try:
        return _to_sqlite(text)
    except DumpError:
        return text


def prepare(content: bytes) -> tuple[str, str]:
    """Decodifica, classifica e prepara o dump para execução.

    Devolve (texto_executável, descrição). Levanta DumpError quando o arquivo
    não contém estrutura de tabelas — sem isso não há schema para consultar.
    """
    texto = decode_dump(content)

    if not has_create(texto):
        raise DumpError(
            "O arquivo não contém CREATE TABLE. Envie um dump com a estrutura "
            "das tabelas (não apenas INSERTs)."
        )

    if looks_like_dump(texto):
        descricao = "dump com dados"
    else:
        descricao = "dump só de estrutura (dados de exemplo serão gerados)"

    if is_mysql_dump(texto):
        descricao += " · convertido do MySQL"

    return normalize_for_sqlite(texto), descricao
