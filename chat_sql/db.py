"""Conector somente-leitura para bancos reais (A IMPLEMENTAR pelo grupo).

Este arquivo e um esqueleto. Siga a Fase 1 do ROADMAP.md.

Roteiro sugerido
----------------
1. Criar a engine SQLAlchemy a partir de `DatabaseConfig.url`
   (ex.: `postgresql+psycopg://user:senha@host/banco`, `mysql+pymysql://...`,
   `sqlite:///caminho/arquivo.db`).
2. Abrir a conexao e confirmar com `SELECT 1`.
3. Introspectar o schema com `sqlalchemy.inspect` (colunas, tipos e foreign keys)
   e montar um `Schema`.
4. Implementar `execute()` reaproveitando a Trava (`guard.validate`) e os limites
   de `config.py` (tempo e numero de linhas).
5. Ativar os testes de `tests/test_db_connector.py`.

Seguranca (obrigatorio)
-----------------------
- Exigir um usuario de banco SOMENTE-LEITURA.
- Nunca executar DDL/DML (a Trava bloqueia, mas nao confie apenas nela).
- Aplicar timeout e limite de linhas.

Dependencia: `sqlalchemy` (adicionar ao requirements.txt ao implementar).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .engine import QueryResult
from .schema import Schema


@dataclass
class DatabaseConfig:
    """Dados de conexao informados pela Instituicao."""

    url: str
    allowed_tables: list[str] = field(default_factory=list)


class DatabaseSource:
    """Fonte de Dados apoiada em um banco real, somente leitura."""

    def __init__(self, config: DatabaseConfig) -> None:
        raise NotImplementedError(
            "Esqueleto: implemente o conector de banco real (ROADMAP.md, Fase 1)."
        )

    @property
    def schema(self) -> Schema:  # pragma: no cover - esqueleto
        raise NotImplementedError

    def execute(
        self, sql: str, *, max_rows: int = 1000, timeout: float = 5.0
    ) -> QueryResult:  # pragma: no cover - esqueleto
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover - esqueleto
        raise NotImplementedError
