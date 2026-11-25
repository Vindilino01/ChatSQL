"""Fontes de dados novas: Google Sheets e upload de dump .sql."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from chat_sql import store

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path / "sources")


def test_todas_as_fontes_aparecem():
    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    opcoes = app.radio[0].options
    assert "Google Sheets (link público)" in opcoes
    assert "Arquivo .sql (dump)" in opcoes
    assert len(opcoes) == 6


def test_sheets_sem_link_avisa():
    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    app.radio[0].set_value("Google Sheets (link público)").run()
    app.button(key="load_sheets").click().run()
    assert not app.exception
    assert any("Cole o link" in w.value for w in app.warning)


def test_dump_sem_arquivo_avisa():
    app = AppTest.from_file(APP, default_timeout=60)
    app.run()
    app.radio[0].set_value("Arquivo .sql (dump)").run()
    app.button(key="load_dump").click().run()
    assert not app.exception
    assert any("Envie um arquivo" in w.value for w in app.warning)


def test_dump_com_estrutura_carrega_e_pergunta():
    """Fluxo completo: enviar um dump só de estrutura e perguntar."""
    script = (
        "CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT NOT NULL);\n"
        "CREATE TABLE vendas (id INTEGER PRIMARY KEY, cliente_id INTEGER, valor REAL);"
    )

    # O file_uploader do AppTest não aceita upload; exercitamos o caminho
    # equivalente validando decode + schema + banco, que é o que o botão faz.
    from chat_sql.engine import InMemoryDatabase
    from chat_sql.sample_data import generate_sample_data
    from chat_sql.schema import parse_schema
    from chat_sql.sql_dump import prepare

    texto, descricao = prepare(script.encode("utf-8"))
    assert "estrutura" in descricao

    schema = parse_schema(texto)
    assert set(schema.table_names()) == {"clientes", "vendas"}

    data = generate_sample_data(schema, 10)
    db = InMemoryDatabase(schema, data)
    assert db.execute("SELECT COUNT(*) FROM clientes;").rows[0][0] == 10


def _rodar_acao(acao: str, preparar: str = "") -> AppTest:
    """Roda uma função do app uma única vez, dentro de um AppTest.

    O `file_uploader` do AppTest não aceita upload (a chave é resetada no
    render), e as funções de carga terminam em `st.rerun()`. Aqui o estado é
    montado e a função é chamada direto; a guarda por `source_label` impede o
    laço infinito, já que o script rodaria de novo após o rerun.
    """
    raiz = str(Path(__file__).resolve().parents[1])
    script = f"""
import sys
sys.path.insert(0, {raiz!r})
import app as appmod

appmod._init_state()
if not appmod.st.session_state.get("source_label"):
{preparar}
    appmod.{acao}()
"""
    app = AppTest.from_string(script, default_timeout=60)
    app.run()
    return app


def test_load_dump_com_dados_ativa_a_fonte():
    """O caminho do botão: dump enviado -> fonte ativa -> dados reais."""
    dump = (
        "CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT);\n"
        "CREATE TABLE vendas (id INTEGER PRIMARY KEY, cliente_id INTEGER, valor REAL);\n"
        "INSERT INTO clientes VALUES (1, 'Ana'), (2, 'Bob');\n"
        "INSERT INTO vendas VALUES (1, 1, 120.5), (2, 2, 80.0);"
    )
    preparar = f"""
    class _Upload:
        def getvalue(self):
            return {dump.encode("utf-8")!r}

    appmod.st.session_state["dump_file"] = _Upload()
"""
    app = _rodar_acao("_load_dump", preparar)

    assert not app.exception, [str(e.value) for e in app.exception]
    assert not app.error, [e.value for e in app.error]
    assert app.session_state.source_label.startswith("Dump .sql")
    # Os dados vêm do dump (data=None), não de dados de exemplo.
    assert app.session_state.data is None
    assert app.session_state.database.execute(
        "SELECT COUNT(*) FROM clientes;"
    ).rows == [(2,)]
    assert app.session_state.database.execute(
        "SELECT COUNT(*) FROM vendas;"
    ).rows == [(2,)]


def test_load_dump_mysql_pelo_botao():
    """O caso real de migração: dump MySQL carrega pelo caminho do botão."""
    dump = (
        "-- MySQL dump 10.13\n"
        "CREATE TABLE `clientes` (\n"
        "  `id` int(11) NOT NULL AUTO_INCREMENT,\n"
        "  `nome` varchar(120) NOT NULL,\n"
        "  PRIMARY KEY (`id`),\n"
        "  KEY `idx_nome` (`nome`)\n"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;\n"
        "INSERT INTO `clientes` VALUES (1,'Ana'),(2,'Bob');\n"
    )

    preparar = f"""
    class _Upload:
        def getvalue(self):
            return {dump.encode("utf-8")!r}

    appmod.st.session_state["dump_file"] = _Upload()
"""
    app = _rodar_acao("_load_dump", preparar)

    assert not app.exception, [str(e.value) for e in app.exception]
    assert not app.error, [e.value for e in app.error]
    assert "MySQL" in app.session_state.source_label
    assert app.session_state.database.execute(
        "SELECT nome FROM clientes WHERE id = 2;"
    ).rows == [("Bob",)]


def test_load_sheets_ativa_a_fonte():
    """Google Sheets pelo caminho do botão, com o download simulado.

    O download é substituído no módulo: aqui se testa a integração (CSV ->
    tabelas -> schema -> banco -> fonte ativa), não a rede.
    """
    csv = b"nome,idade\nAna,30\nBob,25\n"
    preparar = f'''
    import chat_sql.sheets as sheets_mod
    sheets_mod.urllib.request.urlopen = lambda *a, **k: type(
        "R", (), {{"read": staticmethod(lambda: {csv!r}), "__enter__": lambda s: s, "__exit__": lambda *a: False}}
    )()
    appmod.st.session_state["sheets_url"] = "https://docs.google.com/spreadsheets/d/ABC/edit"
'''
    app = _rodar_acao("_load_sheets", preparar)

    assert not app.exception, [str(e.value) for e in app.exception]
    assert not app.error, [e.value for e in app.error]
    assert app.session_state.source_label == "Google Sheets"
    assert app.session_state.database.execute(
        'SELECT COUNT(*) FROM "google_sheets";'
    ).rows == [(2,)]
    assert app.session_state.database.execute(
        'SELECT nome FROM "google_sheets" WHERE idade = 25;'
    ).rows == [("Bob",)]
