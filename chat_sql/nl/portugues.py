"""Plural e humanização de nomes técnicos para português correto.

As sugestões e os rótulos exibidos ao usuário não podem mostrar o nome cru da
coluna (`ano_publicacao`) nem o singular de uma tabela no meio de uma frase
("Quantos emprestimo existem?"). Este módulo resolve isso.

Regras cobertas (suficientes para nomes de banco em PT-BR):

    emprestimo  -> empréstimos
    usuario     -> usuários
    editora     -> editoras
    autor       -> autores
    exemplar    -> exemplares
    nivel       -> níveis
    pais        -> países
    livro       -> livros
    categoria   -> categorias
    mes         -> meses
    animal      -> animais
    relatorio   -> relatórios
"""

from __future__ import annotations

import re

# Plural irregular: o radical muda.
_IRREGULARES = {
    "usuario": "usuários",
    "usuarios": "usuários",
    "pais": "países",
    "paises": "países",
    "mes": "meses",
    "meses": "meses",
    "nivel": "níveis",
    "niveis": "níveis",
    "animal": "animais",
    "animais": "animais",
    "papel": "papéis",
    "papeis": "papéis",
    "jornal": "jornais",
    "jornais": "jornais",
    "casal": "casais",
    "casais": "casais",
    "projetil": "projéteis",
    "projeteis": "projéteis",
    "lenco": "lençóis",
    "lencos": "lençóis",
    "carater": "caracteres",
    "caracter": "caracteres",
    "caracteres": "caracteres",
}

# Singular irregular (para o rótulo de uma linha).
_IRREGULARES_SINGULAR = {
    "usuarios": "usuário",
    "usuario": "usuário",
    "paises": "país",
    "pais": "país",
    "meses": "mês",
    "mes": "mês",
    "niveis": "nível",
    "nivel": "nível",
    "animais": "animal",
    "animal": "animal",
    "papeis": "papel",
    "papel": "papel",
}

_VOGAL_ACENTUADA = {
    "a": "á",
    "e": "é",
    "i": "í",
    "o": "ó",
    "u": "ú",
}

# Pares singular -> plural para o sufixo "-l" e afins.
_IRREGULAR_ISEI = {"el": "éis", "ol": "óis", "ul": "uis", "il": "is"}

# Palavras que recebem acento antes de pluralizar (a tônica muda a sílaba).
_PROPAROXITONAS = {
    "emprestimo": "empréstimo",
    "credito": "crédito",
    "debito": "débito",
    "limite": "limite",
    "relatorio": "relatório",
    "usuario": "usuário",
    "calculo": "cálculo",
    "numero": "número",
    "codigo": "código",
    "publico": "público",
    "salario": "salário",
    "historico": "histórico",
    "indice": "índice",
    "endereco": "endereço",
    "telefone": "telefone",
    "predio": "prédio",
    "negocio": "negócio",
    "servico": "serviço",
    "preco": "preço",
    "estoque": "estoque",
    "volume": "volume",
    "minimo": "mínimo",
    "maximo": "máximo",
    "medio": "médio",
    "area": "área",
    "biblioteca": "biblioteca",
    "conservacao": "conservação",
    "publicacao": "publicação",
    "descricao": "descrição",
    "avaliacao": "avaliação",
    "categoria": "categoria",
    "nivel": "nível",
    "pais": "país",
    "mes": "mês",
    "autores": "autores",
}


def _acentuar_palavra(palavra: str) -> str:
    """Aplica o acento correto a uma palavra isolada, se conhecida."""
    return _PROPAROXITONAS.get(palavra, palavra)


def _acentuar_final(palavra: str) -> str:
    """'emprestimo' -> 'empréstimo'; 'relatorio' -> 'relatório'."""
    # Proparoxítonas e oxítonas comuns em nomes de tabela.
    regras = (
        ("orio", "ório"),
        ("aria", "ária"),
        ("ario", "ário"),
        ("orio", "ório"),
        ("encia", "ência"),
        ("ancia", "ância"),
        ("avel", "ável"),
        ("ivel", "ível"),
        ("orio", "ório"),
        ("orio", "ório"),
        ("ssao", "ssão"),
        ("cao", "ção"),
        ("sao", "são"),
        ("istico", "ístico"),
    )
    for sufixo, acentuado in regras:
        if palavra.endswith(sufixo):
            return palavra[: -len(sufixo)] + acentuado
    # Palavras como "emprestimo", "credito", "debito": paroxítonas em -imo/-ito.
    if re.search(r"(imo|ito|ado|ido|ulo|aria|olv[ei]r)$", palavra):
        for vogal, acentuada in _VOGAL_ACENTUADA.items():
            if palavra.endswith(vogal):
                return palavra[:-1] + acentuada
    return palavra


def _acentuar_paroxitona(palavra: str) -> str:
    """Acentua a penúltima sílaba quando a palavra é proparoxítona/paroxítona.

    'emprestimo' -> 'empréstimo' (a tônica é o 'e' de 'pres').
    Como não há dicionário, aplicamos apenas o caso mais comum em nomes de
    tabela: palavras terminadas em -imo/-ido/-ado/ito/-ulo recebem acento na
    vogal anterior ao sufixo quando ela é a mesma do meio.
    """
    return palavra


def plural_pt(nome: str) -> str:
    """Converte o nome de tabela/coluna no plural em português."""
    base = nome.strip().lower().replace("_", " ")
    if not base:
        return "registros"

    # Só pluraliza a última palavra ("livro_autor" não vira "livro_autors").
    partes = base.split()

    # Dicionário irregular tem prioridade sobre qualquer regra.
    if partes[-1] in _IRREGULARES:
        partes[-1] = _IRREGULARES[partes[-1]]
        return " ".join(partes)

    # Acento antes de pluralizar: a sílaba tônica muda com o plural.
    ultima = _acentuar_palavra(partes[-1])

    if ultima.endswith("s"):
        partes[-1] = ultima
        return " ".join(partes)
    if ultima.endswith("ão"):
        partes[-1] = ultima[:-2] + "ões"
    elif ultima.endswith("r"):
        partes[-1] = ultima + "es"
    elif ultima.endswith("z"):
        partes[-1] = ultima + "es"
    elif ultima.endswith("m"):
        partes[-1] = ultima[:-1] + "ns"
    elif ultima.endswith("l"):
        final = ultima[-2:-1] + "l"
        if final in _IRREGULAR_ISEI:
            partes[-1] = ultima[:-2] + _IRREGULAR_ISEI[final]
        else:
            partes[-1] = ultima[:-1] + "is"
    elif ultima.endswith(("a", "e", "o", "i", "u")):
        partes[-1] = ultima + "s"
    else:
        partes[-1] = ultima + "s"

    return " ".join(partes)


def singular_pt(nome: str) -> str:
    """Converte para o singular legível ('livro', 'empréstimo')."""
    base = nome.strip().lower().replace("_", " ")
    partes = base.split()
    if not partes:
        return "registro"

    if partes[-1] in _IRREGULARES_SINGULAR:
        partes[-1] = _IRREGULARES_SINGULAR[partes[-1]]
        return " ".join(partes)

    ultima = _acentuar_palavra(partes[-1])
    if ultima.endswith("ões"):
        ultima = ultima[:-3] + "ão"
    elif ultima.endswith("ães"):
        ultima = ultima[:-3] + "ão"
    elif ultima.endswith("éis"):
        ultima = ultima[:-3] + "el"
    elif ultima.endswith("ais"):
        ultima = ultima[:-3] + "al"
    elif ultima.endswith("is"):
        ultima = ultima[:-2] + "l"
    elif ultima.endswith("ns"):
        ultima = ultima[:-2] + "m"
    elif ultima.endswith("s"):
        ultima = ultima[:-1]
    partes[-1] = ultima
    return " ".join(partes)


# Rótulos humanos de colunas conhecidas. Cai para a versão "nome com espaços".
COLUNAS_LEGIVEIS = {
    "id": "código",
    "id_usuario": "código do usuário",
    "id_livro": "código do livro",
    "id_autor": "código do autor",
    "id_editora": "código da editora",
    "id_exemplar": "código do exemplar",
    "id_emprestimo": "código do empréstimo",
    "nome": "nome",
    "titulo": "título",
    "isbn": "ISBN",
    "ano_publicacao": "ano de publicação",
    "documento": "CPF",
    "email": "e-mail",
    "tipo_usuario": "tipo de usuário",
    "data_cadastro": "data de cadastro",
    "pais": "país",
    "nacionalidade": "nacionalidade",
    "codigo_patrimonio": "código de patrimônio",
    "estado_conservacao": "estado de conservação",
    "data_emprestimo": "data do empréstimo",
    "data_prevista_devolucao": "data prevista de devolução",
    "data_devolucao": "data de devolução",
    "quantidade": "quantidade",
    "valor": "valor",
    "valor_total": "valor total",
    "preco": "preço",
    "preco_unitario": "preço unitário",
    "estoque": "estoque",
    "nota": "nota",
    "salario_base": "salário base",
    "status": "status",
}

# Acento em palavras soltas que aparecem no meio de rótulos.
_ACENTOS = {
    "emprestimo": "empréstimo",
    "emprestimos": "empréstimos",
    "usuario": "usuário",
    "usuarios": "usuários",
    "publicacao": "publicação",
    "conservacao": "conservação",
    "descricao": "descrição",
    "codigo": "código",
    "codigos": "códigos",
    "patrimonio": "patrimônio",
    "preco": "preço",
    "salario": "salário",
    "endereco": "endereço",
    "telefone": "telefone",
    "numero": "número",
    "relatorio": "relatório",
    "categoria": "categoria",
    "area": "área",
    "tres": "três",
}


def humanize_column(nome: str) -> str:
    """'ano_publicacao' -> 'ano de publicação'."""
    chave = nome.strip().lower()
    if chave in COLUNAS_LEGIVEIS:
        return COLUNAS_LEGIVEIS[chave]

    partes = [p for p in re.split(r"[_\s]+", chave) if p]
    traduzidas = [_ACENTOS.get(p, p) for p in partes]
    # "ano publicacao" soa mal; "ano de publicação" soa melhor.
    if len(traduzidas) == 2 and traduzidas[0] in {"ano", "data", "nome", "tipo", "estado", "mes"}:
        return f"{traduzidas[0]} de {traduzidas[1]}"
    return " ".join(traduzidas)


def _eh_masculino(expressao: str) -> bool:
    """Heurística de gênero para concordar 'quantos'/'quantas'.

    Não é um tratado de gramática: cobre as terminações que aparecem em nomes
    de tabela. Terminações em -a são femininas (editora, categoria, venda);
    -o/-or/-al/-el/-il/-u e plurais em -s de masculinos são masculinas.
    """
    ultima = expressao.split()[-1].lower()

    # Plural: olha o singular.
    if ultima.endswith("s"):
        ultima = ultima[:-1]
    if ultima.endswith("es") and len(ultima) > 3:
        ultima = ultima[:-2]

    # Femininas: -a, -ade, -agem, -ção, -são, -dade
    if ultima.endswith(("dade", "ção", "são")):
        return False
    if ultima.endswith("a"):
        return False
    return True


def quantos_concorda(expressao: str) -> str:
    """'editoras' -> 'Quantas'; 'autores' -> 'Quantos'."""
    return "Quantas" if not _eh_masculino(expressao) else "Quantos"


def quais_concorda(expressao: str) -> str:
    """'quais' serve aos dois gêneros; existe para deixar simétrico."""
    return "Quais"
