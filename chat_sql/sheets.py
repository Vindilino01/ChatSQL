"""Leitura de Google Sheets público.

Uma planilha compartilhada como "qualquer pessoa com o link pode ver" é
baixável como CSV trocando a URL de edição por uma URL de export. Não exige
OAuth, chave de API nem login — que é o ponto: o visitante cola o link e pronto.

Formatos aceitos:
    https://docs.google.com/spreadsheets/d/<ID>/edit#gid=0
    https://docs.google.com/spreadsheets/d/<ID>/edit?usp=sharing
    https://docs.google.com/spreadsheets/d/<ID>/
    https://docs.google.com/spreadsheets/d/<ID>/export?format=csv

A URL gerada omite o `gid`, então baixa a **primeira aba**. Para baixar uma aba
específica, acrescente `&gid=<numero>`.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request

_ID_PATTERN = re.compile(r"/spreadsheets/d/([a-zA-Z0-9_-]+)")
_GID_PATTERN = re.compile(r"[#&?]gid=(\d+)")

TIMEOUT_SEGUNDOS = 20


class SheetsError(Exception):
    """Falha ao baixar a planilha."""


def export_url(sheet_url: str) -> str:
    """Converte um link de edição do Google Sheets na URL de export CSV.

    Levanta SheetsError se a URL não for de uma planilha do Google.
    """
    if not sheet_url or "docs.google.com/spreadsheets" not in sheet_url:
        raise SheetsError(
            "Cole o link de uma planilha do Google (docs.google.com/spreadsheets/...)."
        )

    match = _ID_PATTERN.search(sheet_url)
    if not match:
        raise SheetsError("Não consegui identificar o ID da planilha no link.")

    planilha_id = match.group(1)
    base = f"https://docs.google.com/spreadsheets/d/{planilha_id}/export?format=csv"

    # Preserva a aba escolhida, quando o link traz gid (o "gid=0" da primeira aba).
    gid = _GID_PATTERN.search(sheet_url)
    if gid:
        base += f"&gid={gid.group(1)}"
    return base


def read_public_sheet(sheet_url: str, name: str = "planilha") -> list[tuple[str, bytes]]:
    """Baixa a planilha pública e devolve [(nome, conteudo_csv_em_bytes)].

    O formato de retorno é o mesmo de `spreadsheet.read_tables`, então o
    resultado entra no app sem nenhuma conversão.
    """
    url = sheet_url if "export?format=csv" in sheet_url else export_url(sheet_url)

    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SEGUNDOS) as resposta:
            conteudo = resposta.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise SheetsError(
                "A planilha não está pública. No Google Sheets, use "
                "Compartilhar → Qualquer pessoa com o link → Leitor."
            ) from exc
        if exc.code == 404:
            raise SheetsError("Planilha não encontrada. Confira o link.") from exc
        raise SheetsError(f"O Google respondeu com erro {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise SheetsError(f"Não foi possível acessar a planilha: {exc.reason}") from exc

    if not conteudo:
        raise SheetsError("A planilha veio vazia.")

    # Se o Google devolver HTML, é a tela de login: a planilha não é pública.
    inicio = conteudo[:200].lower()
    if b"<html" in inicio or b"<!doctype" in inicio:
        raise SheetsError(
            "O Google devolveu uma página de login. A planilha precisa estar "
            "pública: Compartilhar → Qualquer pessoa com o link → Leitor."
        )

    return [(f"{name}.csv", conteudo)]
