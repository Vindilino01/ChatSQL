from __future__ import annotations

from pathlib import Path

import pytest

from chat_sql import store
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path / "sources")


def test_app_renders_without_exception():
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception
    assert len(app.tabs) == 3


def test_app_shows_empty_source_hint():
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert any("Fonte de dados" in markdown.value for markdown in app.markdown)


def test_database_source_option_is_available():
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert "Banco de dados (Postgres/SQLite)" in app.radio[0].options


def test_connect_sqlite_end_to_end(tmp_path):
    import sqlite3

    db_path = tmp_path / "loja.db"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        "CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT);"
        "INSERT INTO clientes (id, nome) VALUES (1, 'Ana'), (2, 'Bob');"
    )
    connection.commit()
    connection.close()

    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    app.radio[0].set_value("Banco de dados (Postgres/SQLite)").run()
    app.text_input(key="db_url").set_value(f"sqlite:///{db_path.as_posix()}").run()
    app.button(key="connect_db").click().run()
    assert not app.exception
    assert app.session_state.source_label.startswith("Banco:")

    app.text_input(key="question_input").set_value("quantos clientes existem").run()
    app.button(key="FormSubmitter:pergunta_form-Perguntar").click().run()
    execute_keys = [b.key for b in app.button if b.key and b.key.startswith("execute_")]
    app.button(key=execute_keys[-1]).click().run()
    assert not app.exception
    assert any(metric.label == "Linhas" for metric in app.metric)


def test_full_offline_flow():
    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    app.radio[0].set_value("Schema de exemplo").run()
    app.button(key="load_example").click().run()
    assert any("Fonte ativa" in success.value for success in app.success)

    app.text_input(key="question_input").set_value("quantos clientes existem").run()
    app.button(key="FormSubmitter:pergunta_form-Perguntar").click().run()
    assert not app.exception
    assert app.code  # SQL gerado

    app.button(key="execute_0").click().run()
    assert not app.exception
    assert len(app.dataframe) >= 1
    assert any(metric.label == "Linhas" for metric in app.metric)
