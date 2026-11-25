"""Conexão salvável (C3) e seletor visual de tabelas (C4)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from chat_sql import store

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path / "sources")


def _app():
    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    app.radio[0].set_value("Banco de dados (Postgres/SQLite)").run()
    return app


def test_campos_separados_aparecem_por_padrao():
    app = _app()
    assert not app.exception
    chaves = {item.key for item in app.text_input}
    assert {"db_host", "db_banco", "db_usuario", "db_senha"} <= chaves
    # A senha nunca é exibida em texto puro (proto.type 1 = PASSWORD).
    senha = next(item for item in app.text_input if item.key == "db_senha")
    assert senha.proto.type == 1


def test_url_completa_alterna_o_formulario():
    app = _app()
    app.radio(key="db_input_mode").set_value("URL completa").run()
    chaves = {item.key for item in app.text_input}
    assert "db_url" in chaves
    assert "db_senha" not in chaves


def test_conexao_sem_campos_avisa():
    app = _app()
    app.button(key="connect_db").click().run()
    assert not app.exception
    assert any("Preencha o host" in w.value for w in app.warning)


def test_salva_host_banco_usuario_sem_senha(tmp_path):
    app = _app()
    app.text_input(key="db_host").set_value("ep-teste.neon.tech").run()
    app.text_input(key="db_banco").set_value("neondb").run()
    app.text_input(key="db_usuario").set_value("chatsql_ro").run()
    app.text_input(key="db_senha").set_value("segredo123").run()

    # A conexão vai falhar (host inexistente), mas nada deve quebrar a página
    # nem gravar a senha.
    app.button(key="connect_db").click().run()
    assert not app.exception

    arquivo = store.STORE_DIR / "conexao.json"
    assert arquivo.exists()
    conteudo = arquivo.read_text(encoding="utf-8")
    dados = json.loads(conteudo)
    assert dados["host"] == "ep-teste.neon.tech"
    assert dados["banco"] == "neondb"
    assert dados["usuario"] == "chatsql_ro"
    assert "segredo123" not in conteudo
    assert "senha" not in dados


def test_conexao_salva_preenche_os_campos(tmp_path):
    pasta = store.STORE_DIR
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "conexao.json").write_text(
        json.dumps({"host": "h.neon.tech", "banco": "neondb", "usuario": "chatsql_ro"}),
        encoding="utf-8",
    )

    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    app.radio[0].set_value("Banco de dados (Postgres/SQLite)").run()

    assert app.text_input(key="db_host").value == "h.neon.tech"
    assert app.text_input(key="db_banco").value == "neondb"
    assert app.text_input(key="db_usuario").value == "chatsql_ro"
    assert app.text_input(key="db_senha").value == ""


def test_arquivo_de_conexao_corrompido_nao_quebra(tmp_path):
    pasta = store.STORE_DIR
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "conexao.json").write_text("{isso nao e json", encoding="utf-8")

    app = _app()
    assert not app.exception
    assert app.text_input(key="db_host").value == ""


@pytest.fixture
def banco_sqlite(tmp_path):
    caminho = tmp_path / "demo.db"
    conexao = sqlite3.connect(caminho)
    conexao.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT)")
    conexao.execute("CREATE TABLE vendas (id INTEGER PRIMARY KEY, valor REAL)")
    conexao.executemany("INSERT INTO clientes VALUES (?, ?)", [(1, "Ana"), (2, "Bob")])
    conexao.commit()
    conexao.close()
    return caminho


def test_seletor_de_tabelas_aparece_depois_de_conectar(banco_sqlite):
    app = _app()
    app.radio(key="db_input_mode").set_value("URL completa").run()
    app.text_input(key="db_url").set_value(f"sqlite:///{banco_sqlite.as_posix()}").run()
    app.button(key="connect_db").click().run()

    assert not app.exception
    # Depois de conectar, os nomes ficam conhecidos para a próxima vez.
    disponiveis = app.session_state.db_tabelas_disponiveis
    assert disponiveis == ["clientes", "vendas"]

    # Na tela seguinte, o seletor visual aparece com um checkbox por tabela.
    chaves = {item.key for item in app.checkbox}
    assert {"tbl_clientes", "tbl_vendas"} <= chaves


def test_seletor_restringe_tabelas(banco_sqlite):
    from chat_sql.db import DatabaseConfig, DatabaseSource

    fonte = DatabaseSource(
        DatabaseConfig(url=f"sqlite:///{banco_sqlite.as_posix()}", allowed_tables=["clientes"])
    )
    try:
        assert fonte.schema.table_names() == ["clientes"]
    finally:
        fonte.close()


def test_tabela_desmarcada_nao_desaparece_do_seletor(banco_sqlite):
    """Regressão: conectar filtrando não pode apagar a tabela da lista."""
    app = _app()
    app.radio(key="db_input_mode").set_value("URL completa").run()
    app.text_input(key="db_url").set_value(f"sqlite:///{banco_sqlite.as_posix()}").run()
    app.button(key="connect_db").click().run()
    assert not app.exception

    # Agora desmarca `vendas` e reconecta.
    app.checkbox(key="tbl_vendas").set_value(False).run()
    app.button(key="connect_db").click().run()
    assert not app.exception

    # `vendas` sumiu da fonte ativa, mas continua no seletor para ser religada.
    assert app.session_state.db_tabelas_disponiveis == ["clientes", "vendas"]
    assert {item.key for item in app.checkbox} >= {"tbl_clientes", "tbl_vendas"}


def test_nenhuma_tabela_marcada_avisa_em_vez_de_liberar_tudo(banco_sqlite):
    app = _app()
    app.radio(key="db_input_mode").set_value("URL completa").run()
    app.text_input(key="db_url").set_value(f"sqlite:///{banco_sqlite.as_posix()}").run()
    app.button(key="connect_db").click().run()

    app.checkbox(key="tbl_clientes").set_value(False).run()
    app.checkbox(key="tbl_vendas").set_value(False).run()
    app.button(key="connect_db").click().run()

    assert not app.exception
    assert any("Marque ao menos uma" in w.value for w in app.warning)
