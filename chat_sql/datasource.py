"""Interface comum de Fonte de Dados.

Uma Fonte de Dados é a origem consultável de uma sessão. Hoje existem três tipos:
uma Planilha, um Script SQL ou uma Conexão. As duas primeiras já são atendidas por
`InMemoryDatabase` (chat_sql/engine.py); a terceira é atendida por
`DatabaseSource` (chat_sql/db.py).

Contrato
--------
Toda Fonte de Dados precisa:
1. descrever o próprio Schema (`schema`) para a Trava e para o prompt;
2. executar uma Consulta somente leitura (`execute`) e devolver `QueryResult`;
3. liberar recursos (`close`).

`InMemoryDatabase` já cumpre esta interface (ver tests/test_datasource.py).
"""

from __future__ import annotations

from typing import Protocol

from .engine import QueryResult
from .schema import Schema


class DataSource(Protocol):
    @property
    def schema(self) -> Schema:
        """O Schema da Sessão desta fonte (tabelas, colunas e chaves estrangeiras)."""
        ...

    def execute(self, sql: str, *, max_rows: int = 1000, timeout: float = 5.0) -> QueryResult:
        """Executa uma Consulta ja aprovada pela Trava e devolve as linhas."""
        ...

    def close(self) -> None:
        """Libera a conexão e os recursos."""
        ...
