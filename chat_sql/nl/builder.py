"""Montagem de SQL com resolucao de junções por BFS no grafo de FKs."""

from __future__ import annotations

from collections import deque

from ..schema import Schema, Table
from .text import quote

Edge = tuple[str, str, str, str]  # (left_table, left_col, right_table, right_col)


def graph_edges(schema: Schema) -> list[Edge]:
    edges: list[Edge] = []
    for table in schema.tables.values():
        for fk in table.foreign_keys:
            parent = schema.table(fk.ref_table)
            if parent is None:
                continue
            for index, column in enumerate(fk.columns):
                ref = fk.ref_columns[index] if index < len(fk.ref_columns) else (
                    parent.primary_keys[0] if parent.primary_keys else None
                )
                if ref:
                    edges.append((table.name, column, parent.name, ref))
    return edges


def _incident(edges: list[Edge], table: str) -> list[Edge]:
    key = table.lower()
    return [edge for edge in edges if edge[0].lower() == key or edge[2].lower() == key]


def find_path(schema: Schema, included, target: str, edges: list[Edge] | None = None) -> list[Edge] | None:
    edges = edges if edges is not None else graph_edges(schema)
    included_keys = {name.lower() for name in included}
    target_key = target.lower()
    if target_key in included_keys:
        return []
    parent: dict[str, str | None] = {key: None for key in included_keys}
    used: dict[str, Edge] = {}
    queue: deque[str] = deque(included_keys)
    while queue:
        node = queue.popleft()
        for edge in _incident(edges, node):
            left, _, right, _ = edge
            other = (right if left.lower() == node else left).lower()
            if other in parent:
                continue
            parent[other] = node
            used[other] = edge
            if other == target_key:
                path: list[Edge] = []
                current = target_key
                while parent[current] is not None:
                    path.append(used[current])
                    current = parent[current]  # type: ignore[assignment]
                path.reverse()
                return path
            queue.append(other)
    return None


class SqlBuilder:
    def __init__(self, schema: Schema, subject: Table) -> None:
        self._schema = schema
        self._edges = graph_edges(schema)
        self._aliases: dict[str, str] = {subject.name.lower(): "t0"}
        self._tables: list[str] = [subject.name]
        self._joins: list[str] = []
        self._counter = 1

    def reachable(self, table_name: str) -> bool:
        return find_path(self._schema, self._aliases.keys(), table_name, self._edges) is not None

    def ensure(self, table_name: str) -> bool:
        key = table_name.lower()
        if key in self._aliases:
            return True
        path = find_path(self._schema, self._aliases.keys(), table_name, self._edges)
        if path is None:
            return False
        for edge in path:
            self._add_edge(edge)
        return key in self._aliases

    def _add_edge(self, edge: Edge) -> None:
        left, left_col, right, right_col = edge
        left_key, right_key = left.lower(), right.lower()
        if left_key in self._aliases and right_key not in self._aliases:
            new_key, new_table, new_col, base_col = right_key, right, right_col, left_col
            base_alias = self._aliases[left_key]
        elif right_key in self._aliases and left_key not in self._aliases:
            new_key, new_table, new_col, base_col = left_key, left, left_col, right_col
            base_alias = self._aliases[right_key]
        else:
            return
        alias = f"t{self._counter}"
        self._counter += 1
        self._aliases[new_key] = alias
        self._tables.append(new_table)
        self._joins.append(
            f"JOIN {quote(new_table)} AS {alias} ON {alias}.{quote(new_col)} = {base_alias}.{quote(base_col)}"
        )

    def alias(self, table_name: str) -> str | None:
        self.ensure(table_name)
        return self._aliases.get(table_name.lower())

    def col(self, table_name: str, column: str) -> str | None:
        alias = self.alias(table_name)
        if alias is None:
            return None
        return f"{alias}.{quote(column)}"

    def from_clause(self) -> str:
        first = self._tables[0]
        return f"{quote(first)} AS {self._aliases[first.lower()]}"

    def join_clause(self) -> str:
        return " ".join(self._joins)
