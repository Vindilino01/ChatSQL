"""Garante que a Fonte de Dados em memoria cumpre a interface `DataSource`.

Este teste roda de verdade: ele e a prova de que o contrato definido em
`chat_sql/datasource.py` e respeitado. Use-o como modelo ao implementar
`DatabaseSource` (chat_sql/db.py).
"""

from __future__ import annotations

from chat_sql.datasource import DataSource
from chat_sql.engine import InMemoryDatabase
from chat_sql.sample_data import generate_sample_data


def test_in_memory_database_conforms_to_datasource(schema):
    source: DataSource = InMemoryDatabase(schema, generate_sample_data(schema, 5))

    assert source.schema.has_table("clientes")
    result = source.execute("SELECT COUNT(*) FROM clientes;")
    assert result.rows[0][0] == 5

    source.close()
