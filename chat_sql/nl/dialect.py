"""Diferenças de SQL entre os dialetos suportados (SQLite e PostgreSQL).

O Motor Offline monta a Consulta como texto. Funções de data e comparações de
texto mudam de um banco para outro:

| Intenção              | SQLite                                   | PostgreSQL                                    |
|-----------------------|------------------------------------------|-----------------------------------------------|
| hoje                  | `date('now')`                            | `CURRENT_DATE`                                |
| há N meses            | `date('now','-N months')`                | `CURRENT_DATE - INTERVAL 'N months'`          |
| início do mês         | `date('now','start of month')`           | `date_trunc('month', CURRENT_DATE)::date`     |
| mês da coluna         | `strftime('%m', col)`                    | `to_char(col, 'MM')`                          |
| ano da coluna         | `strftime('%Y', col)`                    | `to_char(col, 'YYYY')`                        |
| ano-mês da coluna     | `strftime('%Y-%m', col)`                 | `to_char(col, 'YYYY-MM')`                     |
| só a data             | `date(col)`                              | `col::date`                                   |
| busca sem caixa       | `LIKE` (SQLite já ignora caixa em ASCII) | `ILIKE`                                       |
| boolean               | `1` / `0`                                | `true` / `false`                              |

Para usar um dialeto novo (MySQL, SQL Server...), basta criar outra subclasse
de `Dialect` e registrá-la em `DIALECTS`.
"""

from __future__ import annotations


class Dialect:
    """Produz os trechos de SQL que variam entre bancos."""

    name = "sqlite"

    # -- datas ---------------------------------------------------------

    def current_date(self) -> str:
        """A data de hoje."""
        return "date('now')"

    def days_ago(self, days: int) -> str:
        """A data de N dias atrás."""
        return f"date('now', '-{int(days)} days')"

    def months_ago(self, months: int) -> str:
        """A data de N meses atrás."""
        return f"date('now', '-{int(months)} months')"

    def years_ago(self, years: int) -> str:
        """A data de N anos atrás."""
        return f"date('now', '-{int(years)} years')"

    def start_of_month(self) -> str:
        return "date('now', 'start of month')"

    def start_of_year(self, years_back: int = 0) -> str:
        if years_back:
            return f"date('now', 'start of year', '-{int(years_back)} year')"
        return "date('now', 'start of year')"

    def month_number(self, column: str) -> str:
        return f"strftime('%m', {column})"

    def year_number(self, column: str) -> str:
        return f"strftime('%Y', {column})"

    def year_month(self, column: str) -> str:
        return f"strftime('%Y-%m', {column})"

    def date_only(self, column: str) -> str:
        return f"date({column})"

    def month_between(self, column: str, first: int, last: int) -> str:
        """Condição para o mês da coluna estar entre dois números."""
        return f"CAST({self.month_number(column)} AS INTEGER) BETWEEN {first} AND {last}"

    # -- texto e booleanos --------------------------------------------

    def like(self) -> str:
        """Operador de comparação de texto com curinga."""
        return "LIKE"

    def boolean(self, value: bool) -> str:
        return "1" if value else "0"


class PostgresDialect(Dialect):
    """Ajustes para PostgreSQL (usado na demo da biblioteca)."""

    name = "postgres"

    def current_date(self) -> str:
        return "CURRENT_DATE"

    def days_ago(self, days: int) -> str:
        return f"(CURRENT_DATE - INTERVAL '{int(days)} days')"

    def months_ago(self, months: int) -> str:
        return f"(CURRENT_DATE - INTERVAL '{int(months)} months')"

    def years_ago(self, years: int) -> str:
        return f"(CURRENT_DATE - INTERVAL '{int(years)} years')"

    def start_of_month(self) -> str:
        return "date_trunc('month', CURRENT_DATE)::date"

    def start_of_year(self, years_back: int = 0) -> str:
        base = "date_trunc('year', CURRENT_DATE)::date"
        if years_back:
            return f"({base} - INTERVAL '{int(years_back)} year')"
        return base

    def month_number(self, column: str) -> str:
        return f"to_char({column}, 'MM')"

    def year_number(self, column: str) -> str:
        return f"to_char({column}, 'YYYY')"

    def year_month(self, column: str) -> str:
        return f"to_char({column}, 'YYYY-MM')"

    def date_only(self, column: str) -> str:
        return f"{column}::date"

    def month_between(self, column: str, first: int, last: int) -> str:
        return f"CAST(to_char({column}, 'MM') AS INTEGER) BETWEEN {first} AND {last}"

    def like(self) -> str:
        # No Postgres, LIKE diferencia maiúsculas; ILIKE faz a busca sem caixa.
        return "ILIKE"

    def boolean(self, value: bool) -> str:
        return "true" if value else "false"


DIALECTS: dict[str, type[Dialect]] = {
    "sqlite": Dialect,
    "postgres": PostgresDialect,
    "postgresql": PostgresDialect,
}

ALIASES = {"postgresql": "postgres", "postgres": "postgres", "sqlite": "sqlite"}


def get_dialect(name: str | None) -> Dialect:
    """Devolve o dialeto pedido; usa SQLite quando não reconhece o nome."""
    key = (name or "sqlite").strip().lower()
    return DIALECTS.get(key, Dialect)()


def normalize_name(name: str | None) -> str:
    """Nome canônico do dialeto ('postgres' ou 'sqlite')."""
    key = (name or "sqlite").strip().lower()
    return ALIASES.get(key, "sqlite")
