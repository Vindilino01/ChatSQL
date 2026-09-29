from __future__ import annotations

from chat_sql.sample_data import generate_sample_data


def test_deterministic_for_same_schema(schema):
    first = generate_sample_data(schema, 30)
    second = generate_sample_data(schema, 30)
    assert first.rows == second.rows


def test_different_seed_changes_data(schema):
    first = generate_sample_data(schema, 30, seed=1)
    second = generate_sample_data(schema, 30, seed=2)
    assert first.rows != second.rows


def test_row_counts(data):
    assert set(data.rows) == {"categorias", "clientes", "produtos", "pedidos", "itens_pedido"}
    for rows in data.rows.values():
        assert len(rows) == 50


def _rows_for(data, name: str):
    for table_name, rows in data.rows.items():
        if table_name.lower() == name.lower():
            return rows
    raise AssertionError(f"Tabela {name} nao encontrada nos dados gerados.")


def test_foreign_key_integrity(schema, data):
    for table in schema.tables.values():
        for fk in table.foreign_keys:
            parent = _rows_for(data, fk.ref_table)
            for position, column in enumerate(fk.columns):
                ref_column = fk.ref_columns[position] if position < len(fk.ref_columns) else None
                if ref_column is None:
                    continue
                parent_values = {row[ref_column] for row in parent if row.get(ref_column) is not None}
                child_values = {
                    row[column] for row in data.rows[table.name] if row.get(column) is not None
                }
                assert child_values <= parent_values, f"{table.name}.{column} referencia valores inexistentes"
