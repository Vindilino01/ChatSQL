from __future__ import annotations

from chat_sql import store


def test_save_and_read_text(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path)
    source_id = store.save_text("CREATE TABLE t (id INTEGER);", "script", rows=5)
    meta = store.read_source(source_id)
    assert meta is not None
    assert meta["kind"] == "script"
    assert meta["text"].startswith("CREATE TABLE")
    assert meta["rows"] == 5


def test_save_and_read_spreadsheet(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path)
    source_id = store.save_uploaded([("clientes.csv", b"id;nome\n1;Ana\n")])
    meta = store.read_source(source_id)
    assert meta is not None
    assert meta["kind"] == "spreadsheet"
    name, content = meta["files_payload"][0]
    assert name == "clientes.csv"
    assert b"Ana" in content


def test_same_content_same_id(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path)
    first = store.save_text("SELECT 1;", "script")
    second = store.save_text("SELECT 1;", "script")
    assert first == second


def test_clear_all(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path)
    source_id = store.save_text("SELECT 1;", "script")
    assert store.read_source(source_id) is not None
    store.clear_all()
    assert store.read_source(source_id) is None


def test_list_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path)
    store.save_text("SELECT 1;", "script", label="Meu script")
    store.save_uploaded([("a.csv", b"x\n1\n")])
    sources = store.list_sources()
    assert len(sources) == 2
    labels = {source["label"] for source in sources}
    assert "Meu script" in labels


def test_turns_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path)
    source_id = store.save_text("SELECT 1;", "script")
    store.save_turns(source_id, [{"question": "q", "sql": "SELECT 1;", "executed": True}])
    turns = store.read_turns(source_id)
    assert len(turns) == 1
    assert turns[0]["question"] == "q"


def test_recent_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE_DIR", tmp_path)
    source_id = store.save_text("SELECT 1;", "script")
    store.save_recent(source_id, ["primeira", "segunda"])
    assert store.read_recent(source_id) == ["primeira", "segunda"]


def test_read_turns_missing_returns_empty():
    assert store.read_turns("nao-existe") == []
    assert store.read_recent("nao-existe") == []


def test_missing_source_returns_none():
    assert store.read_source("nao-existe") is None
    assert store.read_source("../etc/passwd") is None
