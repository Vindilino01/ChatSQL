"""Filtro de nacionalidade do Motor Offline.

Antes desta correção, "quantos autores brasileiros existem" devolvia **277** —
a contagem inteira, sem filtro e sem aviso. O motor reconhecia valores de
domínio de `usuario` e `exemplar`, mas não a coluna `nacionalidade`.
"""

from __future__ import annotations

import pytest

from chat_sql.nl.gentilicos import GENTILICOS, PAISES, pais_do_gentilico, pais_pelo_nome
from chat_sql.nl.text import normalize
from chat_sql.schema import parse_schema
from chat_sql.offline import OfflineEngine

DDL = """
CREATE TABLE autor (id_autor INTEGER PRIMARY KEY, nome TEXT NOT NULL, nacionalidade TEXT);
CREATE TABLE livro (id_livro INTEGER PRIMARY KEY, titulo TEXT NOT NULL, id_editora INTEGER);
CREATE TABLE livro_autor (id_livro INTEGER NOT NULL, id_autor INTEGER NOT NULL, PRIMARY KEY (id_livro, id_autor));
CREATE TABLE editora (id_editora INTEGER PRIMARY KEY, nome TEXT NOT NULL, pais TEXT);
CREATE TABLE usuario (id_usuario INTEGER PRIMARY KEY, nome TEXT NOT NULL);
CREATE TABLE exemplar (id_exemplar INTEGER PRIMARY KEY, id_livro INTEGER);
CREATE TABLE emprestimo (id_emprestimo INTEGER PRIMARY KEY, id_usuario INTEGER, id_exemplar INTEGER);
"""


@pytest.fixture(scope="module")
def schema():
    return parse_schema(DDL)


@pytest.fixture(scope="module")
def engine():
    return OfflineEngine(dialect="postgres")


@pytest.mark.parametrize(
    ("pergunta", "pais"),
    [
        ("quantos autores brasileiros existem", "Brasil"),
        ("autores brasileiros", "Brasil"),
        ("quantos autores de Portugal", "Portugal"),
        ("autores franceses", "França"),
        ("quantos autores alemães", "Alemanha"),
        ("autores do Reino Unido", "Reino Unido"),
        ("quantos autores dos Estados Unidos", "Estados Unidos"),
        ("quais autores são de Moçambique", "Moçambique"),
        ("autores da Suíça", "Suíça"),
        ("quantos autores chineses", "China"),
    ],
)
def test_filtra_por_pais_ou_gentilico(engine, schema, pergunta, pais):
    sql = engine.generate_sql(pergunta, schema)
    assert sql, f"não gerou SQL para {pergunta!r}: {engine.last_reason}"
    assert "nacionalidade" in sql
    assert f"'{pais}'" in sql, sql


def test_gentilico_e_nome_do_pais_dao_o_mesmo_sql(engine, schema):
    por_gentilico = engine.generate_sql("autores brasileiros", schema)
    por_nome = engine.generate_sql("autores do Brasil", schema)
    assert por_gentilico == por_nome


def test_sem_filtro_nao_inventa_pais(engine, schema):
    """`existem` não pode ser confundido com nome de país."""
    sql = engine.generate_sql("quantos autores existem", schema)
    assert sql
    assert "WHERE" not in sql.upper()


def test_agrupamento_tem_prioridade(engine, schema):
    sql = engine.generate_sql("distribuição de autores por nacionalidade", schema)
    assert sql
    assert "GROUP BY" in sql.upper()
    assert "WHERE" not in sql.upper()


def test_pais_fora_do_acervo_nao_filtra_errado(engine, schema):
    """Se o país não está na lista, o motor não deve inventar um filtro."""
    sql = engine.generate_sql("quantos autores existem", schema)
    assert "nacionalidade" not in sql


def test_gentilicos_mapeiam_para_paises_reais():
    """Todo valor do mapa tem de ser um nome que existe no banco."""
    from scripts.acervo_biblioteca import EDITORAS
    from scripts.acervo_nacionalidades import NACIONALIDADE_AUTORES

    paises_do_banco = set(NACIONALIDADE_AUTORES.values()) | {p for _, p in EDITORAS}
    invalidos = sorted({pais for pais in GENTILICOS.values() if pais not in paises_do_banco})
    assert not invalidos, f"gentílicos apontando para país inexistente: {invalidos}"

    invalidos = sorted({pais for pais in PAISES.values() if pais not in paises_do_banco})
    assert not invalidos, f"nomes apontando para país inexistente: {invalidos}"


def test_gentilicos_resistem_a_normalizacao():
    """O motor normaliza a pergunta (sem acento); o mapa precisa casar."""
    for palavra in ("francês", "alemã", "inglês", "português", "moçambicano", "chinês"):
        assert pais_do_gentilico(palavra), f"{palavra!r} não casa"


@pytest.mark.parametrize(
    "palavra",
    [
        "brasileiros", "brasileiras",
        "moçambicanos", "franceses", "alemães", "ingleses",
        "portugueses", "chineses", "russos", "suíços",
        "espanhóis", "gregos", "poloneses", "austríacos",
        "canadenses", "israelenses", "australianos", "nigerianos",
    ],
)
def test_plurais_e_acentos_casam(palavra):
    """Cada forma real de pergunta precisa resolver para um país."""
    assert pais_do_gentilico(palavra), f"{palavra!r} -> {normalize(palavra)!r} não casa"


def test_todo_pais_do_acervo_tem_forma_reconhecida():
    """País presente no banco sem gentílico nenhum é uma pergunta que falha.

    Não exige que todos tenham gentílico (o nome do país sempre funciona),
    mas garante que os países com muitos autores tenham — são os que a banca
    vai perguntar.
    """
    from collections import Counter

    from scripts.acervo_nacionalidades import NACIONALIDADE_AUTORES

    contagem = Counter(NACIONALIDADE_AUTORES.values())
    # Todo país com 3+ autores precisa de gentílico.
    for pais, quantidade in contagem.items():
        if quantidade < 3:
            continue
        formas = [forma for forma, alvo in GENTILICOS.items() if alvo == pais]
        assert formas, f"{pais} ({quantidade} autores) não tem gentílico cadastrado"


def test_nome_do_pais_sem_acento():
    assert pais_pelo_nome("mocambique") == "Moçambique"
    assert pais_pelo_nome("Suica") == "Suíça"
    assert pais_pelo_nome("estados unidos") == "Estados Unidos"
    assert pais_pelo_nome("atlantida") is None
