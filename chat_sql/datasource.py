"""Interface comum de Fonte de Dados.

Uma Fonte de Dados e a origem consultavel de uma sessao. Hoje existem tres tipos:
uma Planilha, um Script SQL ou uma Conexao. As duas primeiras ja sao atendidas por
`InMemoryDatabase` (chat_sql/engine.py); a terceira sera implementada em
`DatabaseSource` (chat_sql/db.py) pelo grupo — ver ROADMAP.md, Fase 1.

Contrato
--------
Toda Fonte de Dados precisa:
1. descrever o proprio Schema (`schema`) para a Trava e para o prompt;
2. executar uma Consulta somente-leitura (`execute`) e devolver `QueryResult`;
3. liberar recursos (`close`).

`InMemoryDatabase` ja cumpre esta interface (ver tests/test_datasource.py).
"""

from __future__ import annotations

from typing import Protocol

from .engine import QueryResult
from .schema import Schema


class DataSource(Protocol):
    @property
    def schema(self) -> Schema:
        """O Schema da Sessao desta fonte (tabelas, colunas e chaves estrangeiras)."""
        ...

    def execute(self, sql: str, *, max_rows: int = 1000, timeout: float = 5.0) -> QueryResult:
        """Executa uma Consulta ja aprovada pela Trava e devolve as linhas."""
        ...

    def close(self) -> None:
        """Libera a conexao e os recursos."""
        ...
