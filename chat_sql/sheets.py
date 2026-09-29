"""Leitura de Google Sheets publico (A IMPLEMENTAR pelo grupo).

Uma planilha publica pode ser baixada como CSV trocando a URL de edicao por uma
URL de export:

    https://docs.google.com/spreadsheets/d/<ID>/export?format=csv

O resultado e o mesmo de uma Planilha comum, entao alimenta
`chat_sql/spreadsheet.read_tables` sem nenhuma mudanca.

Tarefa: D1 do ROADMAP.md.
"""

from __future__ import annotations


def export_url(sheet_url: str) -> str:
    """Converte um link de edicao do Google Sheets na URL de export CSV.

    Exemplos aceitos:
    - https://docs.google.com/spreadsheets/d/ABC123/edit#gid=0
    - https://docs.google.com/spreadsheets/d/ABC123/
    """
    raise NotImplementedError("Esqueleto: implemente conforme o ROADMAP.md (tarefa D1).")


def read_public_sheet(sheet_url: str, name: str = "planilha") -> list[tuple[str, bytes]]:
    """Baixa a planilha publica e devolve [(nome, conteudo_csv_em_bytes)]."""
    raise NotImplementedError("Esqueleto: implemente conforme o ROADMAP.md (tarefa D1).")
