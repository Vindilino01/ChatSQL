"""Gentílicos: como o usuário chama o país do autor.

O banco guarda o nome do país (`Brasil`, `Reino Unido`). O bibliotecário
pergunta pelo gentílico (`brasileiro`, `inglês`). Sem esta tradução, a pergunta
"quantos autores brasileiros existem" devolvia **277** — a contagem inteira,
sem filtro, e sem avisar que o filtro foi ignorado.

Duas armadilhas que este módulo resolve:

1. **Acentuação.** O motor normaliza a pergunta (`normalize`), então
   `alemães` chega como `alemaes`. As chaves são normalizadas na construção —
   cadastrar `alemães` com acento não casaria com nada.
2. **Plural.** Listar cada forma à mão já produziu `angalanas` e fez
   `moçambicanos` deixar de casar. Os plurais e femininos são derivados por
   regra, e um teste confere que todo país do acervo tem pelo menos uma forma.

Um país sem gentílico aqui continua respondendo pelo nome ("quantos autores de
Moçambique"); o que falta é só o sinônimo.
"""

from __future__ import annotations

from .text import normalize

# Gentílico masculino singular já normalizado -> nome do país no banco.
# Só o singular precisa ser escrito: as outras formas saem das regras.
_SINGULARES: dict[str, str] = {
    # ---- América do Sul ----
    "brasileiro": "Brasil",
    "argentino": "Argentina",
    "chileno": "Chile",
    "colombiano": "Colômbia",
    "peruano": "Peru",
    # ---- Europa ----
    "portugues": "Portugal",
    "espanhol": "Espanha",
    "frances": "França",
    "italiano": "Itália",
    "alemao": "Alemanha",
    "britanico": "Reino Unido",
    "ingles": "Reino Unido",
    "escoces": "Reino Unido",
    "irlandes": "Irlanda",
    "russo": "Rússia",
    "sovietico": "Rússia",
    "austriaco": "Áustria",
    "suico": "Suíça",
    "holandes": "Países Baixos",
    "grego": "Grécia",
    "polones": "Polônia",
    "tcheco": "República Tcheca",
    "hungaro": "Hungria",
    # ---- América do Norte ----
    "americano": "Estados Unidos",
    "norte-americano": "Estados Unidos",
    "estadunidense": "Estados Unidos",
    "canadense": "Canadá",
    # ---- Ásia ----
    "chines": "China",
    "indiano": "Índia",
    "israelense": "Israel",
    "iraniano": "Irã",
    "libanes": "Líbano",
    # ---- África ----
    "angolano": "Angola",
    "mocambicano": "Moçambique",
    "nigeriano": "Nigéria",
    "egipcio": "Egito",
    "argelino": "Argélia",
    "sul-africano": "África do Sul",
    # ---- Oceania ----
    "australiano": "Austrália",
    # ---- Outros ----
    "jamaicano": "Jamaica",
    "bosnio": "Bósnia e Herzegovina",
    "bielorrusso": "Bielorrússia",
}

# Formas irregulares que nenhuma regra deriva (ou derivaria errado).
_IRREGULARES: dict[str, str] = {
    "alema": "Alemanha",
    "alemas": "Alemanha",
    "alemaes": "Alemanha",
    "alemoes": "Alemanha",
    "espanhois": "Espanha",
    "espanhola": "Espanha",
    "espanholas": "Espanha",
    "portuguesa": "Portugal",
    "portuguesas": "Portugal",
    "francesa": "França",
    "francesas": "França",
    "inglesa": "Reino Unido",
    "inglesas": "Reino Unido",
    "holandesa": "Países Baixos",
    "holandesas": "Países Baixos",
    "polonesa": "Polônia",
    "polonesas": "Polônia",
    "tcheca": "República Tcheca",
    "tchecas": "República Tcheca",
    "hungara": "Hungria",
    "hungaras": "Hungria",
    "suica": "Suíça",
    "suicas": "Suíça",
    "austriaca": "Áustria",
    "austriacas": "Áustria",
    "irlandesa": "Irlanda",
    "irlandesas": "Irlanda",
    "libanesa": "Líbano",
    "libanesas": "Líbano",
    "egipcia": "Egito",
    "egipcias": "Egito",
    "argelina": "Argélia",
    "argelinas": "Argélia",
    "iraniana": "Irã",
    "iranianas": "Irã",
    "grega": "Grécia",
    "gregas": "Grécia",
    "russa": "Rússia",
    "russas": "Rússia",
    "chinesa": "China",
    "chinesas": "China",
}


def _plural(palavra: str) -> str:
    """Plural do português para as terminações que aparecem nos gentílicos."""
    if palavra.endswith(("a", "e", "i", "o", "u")):
        return palavra + "s"
    if palavra.endswith("s"):
        return palavra + "es"
    if palavra.endswith("l"):
        return palavra[:-1] + "is"
    if palavra.endswith("m"):
        return palavra + "ns"
    if palavra.endswith(("r", "z")):
        return palavra + "es"
    return palavra + "s"


def _feminino(palavra: str) -> str | None:
    """Feminino singular, quando a terminação permite derivar."""
    if palavra.endswith("eiro"):
        return palavra[:-1] + "a"
    if palavra.endswith("ano"):
        return palavra[:-1] + "a"
    if palavra.endswith("ino"):
        return palavra[:-1] + "a"
    if palavra.endswith("es"):  # portugues, frances, ingles, holandes...
        return palavra[:-2] + "esa"
    if palavra.endswith("ol"):  # espanhol
        return palavra[:-2] + "ola"
    if palavra.endswith("o"):
        return palavra[:-1] + "a"
    if palavra.endswith("ense"):
        return palavra
    return None


def _construir() -> dict[str, str]:
    mapa: dict[str, str] = {}
    for singular, pais in _SINGULARES.items():
        chave = normalize(singular)
        mapa[chave] = pais
        mapa[_plural(chave)] = pais
        feminino = _feminino(chave)
        if feminino:
            mapa[feminino] = pais
            mapa[_plural(feminino)] = pais
    for forma, pais in _IRREGULARES.items():
        mapa[normalize(forma)] = pais
    return mapa


GENTILICOS: dict[str, str] = _construir()


def pais_do_gentilico(palavra: str) -> str | None:
    """Converte um gentílico no nome do país (aceita com ou sem acento)."""
    chave = normalize(palavra.strip())
    return GENTILICOS.get(chave)


# Nome do país já normalizado (sem acento, minúsculo) -> nome como está no
# banco. Permite "autores de mocambique" e "autores da suica" sem exigir que o
# usuário digite o acento.
PAISES: dict[str, str] = {
    "alemanha": "Alemanha",
    "angola": "Angola",
    "argentina": "Argentina",
    "argelia": "Argélia",
    "australia": "Austrália",
    "austria": "Áustria",
    "bielorrussia": "Bielorrússia",
    "bosnia e herzegovina": "Bósnia e Herzegovina",
    "brasil": "Brasil",
    "canada": "Canadá",
    "chile": "Chile",
    "china": "China",
    "colombia": "Colômbia",
    "egito": "Egito",
    "espanha": "Espanha",
    "estados unidos": "Estados Unidos",
    "franca": "França",
    "grecia": "Grécia",
    "hungria": "Hungria",
    "india": "Índia",
    "ira": "Irã",
    "irlanda": "Irlanda",
    "israel": "Israel",
    "italia": "Itália",
    "jamaica": "Jamaica",
    "libano": "Líbano",
    "mocambique": "Moçambique",
    "nigeria": "Nigéria",
    "paises baixos": "Países Baixos",
    "peru": "Peru",
    "polonia": "Polônia",
    "portugal": "Portugal",
    "reino unido": "Reino Unido",
    "republica tcheca": "República Tcheca",
    "russia": "Rússia",
    "africa do sul": "África do Sul",
    "suica": "Suíça",
}


def pais_pelo_nome(trecho: str) -> str | None:
    """Reconhece o nome do país digitado sem acento ou em minúsculas."""
    return PAISES.get(trecho.strip().lower())
