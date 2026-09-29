"""Gerador deterministico de Dados de Exemplo.

Sem custo de API e reproduzivel: a mesma seed (derivada do DDL) produz sempre
os mesmos dados. Respeita chaves estrangeiras gerando tabelas-pai antes das
filhas e amostrando valores reais das chaves referenciadas.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from faker import Faker

from .schema import Column, Schema, Table


@dataclass
class GeneratedData:
    rows: dict[str, list[dict]]

    def table_names(self) -> list[str]:
        return list(self.rows.keys())

    def row_count(self, table: str) -> int:
        for name, rows in self.rows.items():
            if name.lower() == table.lower():
                return len(rows)
        return 0


def schema_seed(ddl: str) -> int:
    return int(hashlib.sha256(ddl.encode("utf-8")).hexdigest(), 16) % (2**32)


def _topological_order(schema: Schema) -> list[str]:
    deps: dict[str, set[str]] = {key: set() for key in schema.tables}
    for key, table in schema.tables.items():
        for fk in table.foreign_keys:
            ref = fk.ref_table.lower()
            if ref in schema.tables and ref != key:
                deps[key].add(ref)

    order: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(key: str) -> None:
        if key in visited:
            return
        if key in visiting:
            return
        visiting.add(key)
        for dep in sorted(deps[key]):
            visit(dep)
        visiting.discard(key)
        visited.add(key)
        order.append(key)

    for key in schema.tables:
        visit(key)
    return order


def _has(name: str, *keywords: str) -> bool:
    return any(keyword in name for keyword in keywords)


def _call(fake: Faker, *names: str) -> str:
    for name in names:
        method = getattr(fake, name, None)
        if method is not None:
            try:
                return str(method())
            except Exception:
                continue
    return fake.word()


def _random_date(rng: random.Random) -> str:
    today = date.today()
    start = today - timedelta(days=365)
    return (start + timedelta(days=rng.randint(0, (today - start).days))).isoformat()


def _random_datetime(rng: random.Random) -> str:
    today = datetime.now()
    start = today - timedelta(days=365)
    seconds = rng.randint(0, int((today - start).total_seconds()))
    return (start + timedelta(seconds=seconds)).replace(microsecond=0).isoformat(sep=" ")


def _value_for(column: Column, fake: Faker, rng: random.Random):
    name = column.name.lower()
    kind = column.type

    if kind == "INTEGER":
        if _has(name, "quantidade", "qtd", "quantity", "estoque", "stock", "numero", "number", "idade", "age"):
            return rng.randint(1, 100)
        return rng.randint(1, 1000)
    if kind == "REAL":
        return round(rng.uniform(10, 10000), 2)
    if kind == "BOOLEAN":
        return rng.choice([0, 1])
    if kind == "DATE":
        return _random_date(rng)
    if kind == "TIMESTAMP":
        return _random_datetime(rng)
    if kind == "BLOB":
        return None

    if _has(name, "email"):
        return fake.email()
    if _has(name, "telefone", "fone", "phone", "celular", "whatsapp"):
        return _call(fake, "phone_number", "msisdn")
    if _has(name, "cpf"):
        return _call(fake, "cpf")
    if _has(name, "cnpj"):
        return _call(fake, "cnpj")
    if _has(name, "cep", "postal"):
        return _call(fake, "postcode", "postalcode")
    if _has(name, "cidade", "city", "municipio"):
        return fake.city()
    if _has(name, "estado", "uf"):
        return _call(fake, "estado_sigla", "state_abbr")
    if _has(name, "pais", "country"):
        return fake.country()
    if _has(name, "endereco", "address", "logradouro", "rua"):
        return fake.street_address()
    if _has(name, "empresa", "company", "fornecedor"):
        return fake.company()
    if _has(name, "cargo", "role", "funcao", "posicao"):
        return _call(fake, "job")
    if _has(name, "departamento", "department", "setor"):
        return rng.choice(["Vendas", "Financeiro", "RH", "TI", "Marketing", "Operacoes"])
    if _has(name, "categoria", "category", "segmento"):
        return rng.choice(["Premium", "Standard", "Basico", "A", "B", "C"])
    if _has(name, "status", "situacao"):
        return rng.choice(["ativo", "inativo", "pendente", "concluido", "cancelado"])
    if _has(name, "produto", "product", "descricao", "description", "titulo", "title"):
        return fake.catch_phrase()
    if _has(name, "nome", "name", "cliente", "usuario", "responsavel", "vendedor", "funcionario"):
        return fake.name()
    if _has(name, "genero", "sexo"):
        return rng.choice(["M", "F"])
    if _has(name, "plano"):
        return rng.choice(["free", "pro", "enterprise"])
    return fake.word()


def _lower_map(generated: dict[str, list[dict]]) -> dict[str, list[dict]]:
    return {name.lower(): rows for name, rows in generated.items()}


def _resolve_ref_column(
    schema: Schema,
    ref_table: str,
    position: int,
    ref_columns: tuple[str, ...],
) -> str | None:
    if position < len(ref_columns):
        return ref_columns[position]
    parent = schema.table(ref_table)
    if parent and position < len(parent.primary_keys):
        return parent.primary_keys[position]
    return None


def _generate_table(
    table: Table,
    row_count: int,
    base_seed: int,
    generated: dict[str, list[dict]],
    schema: Schema,
) -> list[dict]:
    table_seed = base_seed ^ (hash(table.name.lower()) & 0xFFFFFFFF)
    rng = random.Random(table_seed)
    fake = Faker("pt_BR")
    fake.seed_instance(table_seed)

    by_name = _lower_map(generated)
    pk_columns = table.primary_keys
    rows: list[dict] = []
    is_self = lambda ref: ref.lower() == table.name.lower()

    for index in range(1, row_count + 1):
        row: dict = {column.name: None for column in table.columns}

        for pk in pk_columns:
            column = next((c for c in table.columns if c.name == pk), None)
            if column is None:
                continue
            row[pk] = index if column.type == "INTEGER" else fake.uuid4()

        for fk in table.foreign_keys:
            parent_rows = rows if is_self(fk.ref_table) else by_name.get(fk.ref_table.lower(), [])
            for position, column_name in enumerate(fk.columns):
                if column_name not in row:
                    continue
                ref_column = _resolve_ref_column(schema, fk.ref_table, position, fk.ref_columns)
                values = []
                if ref_column:
                    values = [r.get(ref_column) for r in parent_rows if r.get(ref_column) is not None]
                if values:
                    row[column_name] = rng.choice(values)
                elif is_self(fk.ref_table):
                    row[column_name] = None
                else:
                    row[column_name] = rng.randint(1, max(1, row_count))

        for column in table.columns:
            if row.get(column.name) is not None:
                continue
            if column.primary_key:
                continue
            row[column.name] = _value_for(column, fake, rng)

        rows.append(row)

    return rows


def generate_sample_data(
    schema: Schema,
    row_count: int,
    seed: int | None = None,
) -> GeneratedData:
    base_seed = schema_seed(schema.raw_ddl) if seed is None else seed
    generated: dict[str, list[dict]] = {}
    for key in _topological_order(schema):
        table = schema.tables[key]
        generated[table.name] = _generate_table(table, row_count, base_seed, generated, schema)
    return GeneratedData(rows=generated)
