"""Importacao de arquivo .sql (dump) (A IMPLEMENTAR pelo grupo).

Um dump tipico contem `CREATE TABLE` e `INSERT INTO`. O app ja aceita colar esse
script na aba Dados; esta tarefa adiciona o **upload de arquivo**.

Tarefa: D2 do ROADMAP.md.

Dica: um script com INSERT ja e carregado por `InMemoryDatabase(schema)` (sem
dados de exemplo). Basta decodificar o arquivo e reaproveitar esse caminho.
"""

from __future__ import annotations


def decode_dump(content: bytes) -> str:
    """Decodifica o arquivo tentando UTF-8 e, se falhar, latin-1."""
    raise NotImplementedError("Esqueleto: implemente conforme o ROADMAP.md (tarefa D2).")


def looks_like_dump(text: str) -> bool:
    """Retorna True se o texto tem um `CREATE TABLE` e pelo menos um `INSERT INTO`."""
    raise NotImplementedError("Esqueleto: implemente conforme o ROADMAP.md (tarefa D2).")
