"""Persistencia das fontes de dados em disco.

As fontes ficam em `~/.chat_sql_sources/<id>/` e sobrevivem a reloads e a
reinicios do servidor. O conteudo e identificado por hash, entao reenviar o
mesmo arquivo reutiliza a mesma fonte.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

STORE_DIR = Path.home() / ".chat_sql_sources"


def _hash(parts: list[bytes]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part)
        digest.update(b"\x00")
    return digest.hexdigest()[:16]


def _folder(source_id: str) -> Path | None:
    if not source_id or "/" in source_id or "\\" in source_id or ".." in source_id:
        return None
    return STORE_DIR / source_id


def save_uploaded(files: list[tuple[str, bytes]]) -> str:
    parts: list[bytes] = []
    for name, content in files:
        parts.append(name.encode("utf-8"))
        parts.append(content)
    source_id = _hash(parts)
    folder = _folder(source_id)
    assert folder is not None
    folder.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    for name, content in files:
        safe = Path(name).name
        (folder / safe).write_bytes(content)
        names.append(safe)
    label = "Planilhas: " + ", ".join(names)
    (folder / "meta.json").write_text(
        json.dumps({"kind": "spreadsheet", "files": names, "label": label}), encoding="utf-8"
    )
    return source_id


def save_text(
    text: str,
    kind: str,
    rows: int | None = None,
    name: str | None = None,
    label: str | None = None,
) -> str:
    source_id = _hash([kind.encode("utf-8"), text.encode("utf-8")])
    folder = _folder(source_id)
    assert folder is not None
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "source.sql").write_text(text, encoding="utf-8")
    meta: dict = {"kind": kind, "label": label or name or kind}
    if rows is not None:
        meta["rows"] = rows
    if name is not None:
        meta["name"] = name
    (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return source_id


def list_sources() -> list[dict]:
    if not STORE_DIR.exists():
        return []
    sources: list[dict] = []
    for folder in STORE_DIR.iterdir():
        if not folder.is_dir():
            continue
        meta_path = folder / "meta.json"
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            mtime = folder.stat().st_mtime
        except (OSError, json.JSONDecodeError):
            continue
        sources.append(
            {
                "source_id": folder.name,
                "label": meta.get("label") or folder.name,
                "kind": meta.get("kind"),
                "mtime": mtime,
            }
        )
    sources.sort(key=lambda item: item["mtime"], reverse=True)
    return sources


def clear_all() -> None:
    if STORE_DIR.exists():
        shutil.rmtree(STORE_DIR, ignore_errors=True)


def _read_json(source_id: str, filename: str):
    folder = _folder(source_id)
    if folder is None:
        return None
    path = folder / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(source_id: str, filename: str, payload) -> None:
    folder = _folder(source_id)
    if folder is None or not folder.exists():
        return
    (folder / filename).write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def save_turns(source_id: str, turns: list[dict]) -> None:
    _write_json(source_id, "turns.json", turns)


def read_turns(source_id: str) -> list[dict]:
    data = _read_json(source_id, "turns.json")
    return data if isinstance(data, list) else []


def save_recent(source_id: str, questions: list[str]) -> None:
    _write_json(source_id, "recent.json", questions)


def read_recent(source_id: str) -> list[str]:
    data = _read_json(source_id, "recent.json")
    if isinstance(data, list):
        return [str(item) for item in data]
    return []


def read_source(source_id: str) -> dict | None:
    folder = _folder(source_id)
    if folder is None:
        return None
    meta_path = folder / "meta.json"
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if meta.get("kind") == "spreadsheet":
        files: list[tuple[str, bytes]] = []
        for name in meta.get("files", []):
            path = folder / Path(name).name
            if path.exists():
                files.append((Path(name).name, path.read_bytes()))
        if not files:
            return None
        meta["files_payload"] = files
    else:
        source_path = folder / "source.sql"
        if not source_path.exists():
            return None
        meta["text"] = source_path.read_text(encoding="utf-8")
    return meta
