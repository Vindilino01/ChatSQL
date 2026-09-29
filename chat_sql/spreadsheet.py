"""Leitura de planilhas (CSV/XLSX/XLS): inferencia de schema, limpeza de
formatos brasileiros e carga para o SQLite em memoria.

Uma aba/arquivo vira uma tabela. Chaves estrangeiras sao inferidas a partir de
colunas no formato `algo_id` quando existe uma tabela `algo`/`algos`.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .offline import _strip_accents, singular
from .sample_data import GeneratedData
from .schema import Schema, parse_schema


@dataclass
class LoadedTable:
    name: str
    frame: pd.DataFrame


def _quote(identifier: str) -> str:
    return '"' + str(identifier).replace('"', '""') + '"'


def _sanitize(name: str) -> str:
    value = _strip_accents(str(name).lower())
    value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
    if not value:
        value = "tabela"
    if value[0].isdigit():
        value = "t_" + value
    return value


def _read_csv(content: bytes) -> pd.DataFrame:
    text: str | None = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = content.decode("utf-8", errors="replace")

    sample = text[:5000]
    delimiter = ","
    best = sample.count(",")
    for candidate in (";", "\t", "|"):
        count = sample.count(candidate)
        if count > best:
            delimiter, best = candidate, count
    try:
        return pd.read_csv(io.StringIO(text), sep=delimiter)
    except pd.errors.EmptyDataError as exc:
        raise ValueError("O arquivo CSV esta vazio ou nao tem colunas.") from exc


def _to_numeric(series: pd.Series) -> pd.Series | None:
    text = series.astype(str).str.strip()
    cleaned = text.str.replace(r"(?i)r\$\s*", "", regex=True).str.replace(r"\s", "", regex=True)

    def convert(value) -> str | None:
        if not isinstance(value, str):
            return None
        if value.lower() in ("", "nan", "none", "nat", "null", "<na>"):
            return None
        if "," in value and "." in value:
            if value.rfind(",") > value.rfind("."):
                return value.replace(".", "").replace(",", ".")
            return value.replace(",", "")
        if "," in value:
            return value.replace(",", ".")
        return value

    numeric = pd.to_numeric(cleaned.map(convert, na_action="ignore"), errors="coerce")
    valid = int(numeric.notna().sum())
    total = int(series.notna().sum())
    if total and valid / total >= 0.9:
        return numeric
    return None


_DATE_PATTERN = re.compile(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}")


def _to_datetime(series: pd.Series) -> pd.Series | None:
    text = series.astype(str).str.strip()
    total = int(series.notna().sum())
    if not total:
        return None
    looks_like_date = int(text.str.contains(_DATE_PATTERN).sum())
    if looks_like_date / total < 0.6:
        return None
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if int(parsed.notna().sum()) / total >= 0.9:
        return parsed
    return None


def _coerce_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]

    # Remove colunas de indice/nao nomeadas (comuns em exportacoes de planilha).
    drop = [
        column
        for column in frame.columns
        if column == ""
        or column.lower().startswith("unnamed")
        or column.lower() in {"index", "índice", "indice", "id_indice"}
    ]
    if drop:
        frame = frame.drop(columns=drop)

    # Remove colunas totalmente vazias.
    empty = [column for column in frame.columns if frame[column].isna().all()]
    if empty:
        frame = frame.drop(columns=empty)

    for column in frame.columns:
        series = frame[column]
        if (
            pd.api.types.is_bool_dtype(series)
            or pd.api.types.is_numeric_dtype(series)
            or pd.api.types.is_datetime64_any_dtype(series)
        ):
            continue
        numeric = _to_numeric(series)
        if numeric is not None:
            frame[column] = numeric
            continue
        dates = _to_datetime(series)
        if dates is not None:
            frame[column] = dates
    return frame


def read_tables(files: list[tuple[str, bytes]]) -> list[LoadedTable]:
    """Le uma lista de (nome_do_arquivo, conteudo). Uma tabela por aba/arquivo."""
    tables: list[LoadedTable] = []
    for filename, content in files:
        lower = filename.lower()
        if lower.endswith((".xlsx", ".xls")):
            sheets = pd.read_excel(io.BytesIO(content), sheet_name=None)
            single = len(sheets) == 1
            for sheet_name, frame in sheets.items():
                name = Path(filename).stem if single else sheet_name
                tables.append(LoadedTable(_sanitize(name), _coerce_frame(frame)))
        else:
            frame = _read_csv(content)
            tables.append(LoadedTable(_sanitize(Path(filename).stem), _coerce_frame(frame)))
    return tables


def _sql_type(dtype) -> str:
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_integer_dtype(dtype):
        return "INTEGER"
    if pd.api.types.is_float_dtype(dtype):
        return "REAL"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"
    return "TEXT"


def _fk_target(column: str, table_names: dict[str, LoadedTable]) -> str | None:
    name = column.lower()
    if not name.endswith("_id"):
        return None
    prefix = name[:-3]
    if not prefix or prefix == "id":
        return None
    for candidate in (prefix, prefix + "s", singular(prefix)):
        if candidate in table_names:
            return candidate
    for candidate in table_names:
        if candidate == prefix or singular(candidate) == prefix or candidate.rstrip("s") == prefix:
            return candidate
    return None


def _pk_column(table: LoadedTable) -> str:
    for column in table.frame.columns:
        if column.lower() == "id":
            return column
    return table.frame.columns[0]


def infer_ddl(tables: list[LoadedTable]) -> str:
    names = {table.name.lower(): table for table in tables}
    statements: list[str] = []
    for table in tables:
        primary_key = _pk_column(table)
        column_defs: list[str] = []
        for column in table.frame.columns:
            definition = f"    {_quote(column)} {_sql_type(table.frame[column].dtype)}"
            if column == primary_key:
                definition += " PRIMARY KEY"
            column_defs.append(definition)
        fk_defs: list[str] = []
        for column in table.frame.columns:
            target = _fk_target(column, names)
            if target:
                pk = _pk_column(names[target])
                fk_defs.append(
                    f"    FOREIGN KEY ({_quote(column)}) REFERENCES {_quote(names[target].name)} ({_quote(pk)})"
                )
        body = ",\n".join(column_defs + fk_defs)
        statements.append(f"CREATE TABLE {_quote(table.name)} (\n{body}\n);")
    return "\n\n".join(statements)


def tables_to_schema(tables: list[LoadedTable], ddl: str | None = None) -> Schema:
    if ddl and ddl.strip():
        return parse_schema(ddl)
    return parse_schema(infer_ddl(tables))


def _clean_value(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.isoformat(sep=" ")
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return int(value)
    return value


def tables_to_data(tables: list[LoadedTable], schema: Schema) -> GeneratedData:
    rows: dict[str, list[dict]] = {}
    for table in tables:
        schema_table = schema.table(table.name)
        if schema_table is None:
            continue
        allowed = {column.lower(): column for column in schema_table.column_names}
        records: list[dict] = []
        for _, row in table.frame.iterrows():
            record: dict = {}
            for column in table.frame.columns:
                target = allowed.get(column.lower())
                if target:
                    record[target] = _clean_value(row[column])
            records.append(record)
        rows[schema_table.name] = records
    return GeneratedData(rows=rows)
