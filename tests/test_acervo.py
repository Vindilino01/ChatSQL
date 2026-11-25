"""Integridade dos dados reais do acervo.

Estes testes não tocam no banco: travam os arquivos de dados que alimentam o
seed. Existem porque a nacionalidade já foi sorteada uma vez, produzindo
Machado de Assis nigeriano e Agatha Christie chilena — e ninguém percebeu.
"""

from __future__ import annotations

import re
from collections import Counter

import pytest

from scripts.acervo_biblioteca import EDITORAS, OBRAS
from scripts.acervo_editoras import (
    CATEGORIA_AUTOR,
    EDITORAS_POR_CATEGORIA,
    categoria_da_obra,
    editora_para,
)
from scripts.acervo_nacionalidades import NACIONALIDADE_AUTORES


def _autores() -> set[str]:
    return {autor for _, autores, _ in OBRAS for autor in autores}


# --- nacionalidades ---------------------------------------------------------


def test_todo_autor_tem_nacionalidade():
    faltando = sorted(_autores() - set(NACIONALIDADE_AUTORES))
    assert not faltando, f"autores sem nacionalidade: {faltando}"


def test_nao_ha_nacionalidade_de_autor_inexistente():
    extras = sorted(set(NACIONALIDADE_AUTORES) - _autores())
    assert not extras, f"nacionalidade para autor que não está no acervo: {extras}"


def test_dicionario_sem_chaves_duplicadas():
    """Duas linhas para o mesmo autor: o Python fica com a última, em silêncio."""
    from pathlib import Path

    texto = (
        Path(__file__).resolve().parents[1] / "scripts" / "acervo_nacionalidades.py"
    ).read_text(encoding="utf-8")
    chaves = re.findall(r'^\s{4}"([^"]+)":', texto, re.M)
    duplicadas = {k: n for k, n in Counter(chaves).items() if n > 1}
    assert not duplicadas, f"chaves repetidas no arquivo: {duplicadas}"


@pytest.mark.parametrize(
    ("autor", "pais"),
    [
        ("Machado de Assis", "Brasil"),
        ("Clarice Lispector", "Brasil"),
        ("João Guimarães Rosa", "Brasil"),
    ],
)
def test_autores_brasileiros_estao_como_brasil(autor, pais):
    assert NACIONALIDADE_AUTORES[autor] == pais


def test_nomes_conhecidos_nao_estao_trocados():
    """Os casos que a banca olharia primeiro."""
    assert NACIONALIDADE_AUTORES["Machado de Assis"] == "Brasil"
    assert NACIONALIDADE_AUTORES["Agatha Christie"] == "Reino Unido"
    assert NACIONALIDADE_AUTORES["Albert Camus"] == "França"
    assert NACIONALIDADE_AUTORES["Fiódor Dostoiévski"] == "Rússia"
    assert NACIONALIDADE_AUTORES["Gabriel García Márquez"] == "Colômbia"
    assert NACIONALIDADE_AUTORES["José Saramago"] == "Portugal"
    assert NACIONALIDADE_AUTORES["Mia Couto"] == "Moçambique"
    assert NACIONALIDADE_AUTORES["Chimamanda Ngozi Adichie"] == "Nigéria"


def test_brasileiros_estao_bem_representados():
    """Um acervo de biblioteca brasileira com 12 autores brasileiros em 277
    era o sintoma mais visível do sorteio. O número real é 59 — os EUA têm
    mais (78) porque o acervo inclui muita obra técnica e de não-ficção."""
    contagem = Counter(NACIONALIDADE_AUTORES.values())
    assert contagem["Brasil"] >= 50
    top3 = [pais for pais, _ in contagem.most_common(3)]
    assert "Brasil" in top3


def test_nacionalidades_sao_paises_plausiveis():
    """Nada de valor vazio, número ou string genérica."""
    for autor, pais in NACIONALIDADE_AUTORES.items():
        assert pais and pais == pais.strip(), f"{autor}: {pais!r}"
        assert len(pais) >= 3, f"{autor}: {pais!r}"


# --- editoras ---------------------------------------------------------------


def test_editoras_mapeadas_existem_no_acervo():
    nomes = {nome for nome, _ in EDITORAS}
    usadas = {nome for lista in EDITORAS_POR_CATEGORIA.values() for nome in lista}
    inexistentes = sorted(usadas - nomes)
    assert not inexistentes, f"editoras citadas que não existem: {inexistentes}"


def test_categorias_apontam_para_autores_reais():
    orfaos = sorted(set(CATEGORIA_AUTOR) - _autores())
    assert not orfaos, f"categoria para autor fora do acervo: {orfaos}"


def test_toda_obra_recebe_editora_valida():
    nomes = {nome for nome, _ in EDITORAS}
    for titulo, autores, _ in OBRAS:
        escolhida = editora_para(titulo, autores)
        assert escolhida in nomes, f"{titulo}: editora {escolhida!r} não existe"


def test_editora_e_deterministica():
    """Rodar o seed duas vezes tem de produzir o mesmo banco."""
    for titulo, autores, _ in OBRAS[:30]:
        assert editora_para(titulo, autores) == editora_para(titulo, autores)


def test_obra_de_computacao_nao_cai_em_editora_de_poesia():
    """O caso que apareceu na tela: `1984` estava na Artmed."""
    assert categoria_da_obra("Clean Code", ("Robert C. Martin",)) == "computacao"
    assert editora_para("Clean Code", ("Robert C. Martin",)) in (
        EDITORAS_POR_CATEGORIA["computacao"]
    )
    assert categoria_da_obra("1984", ("George Orwell",)) == "literatura"


def test_toda_obra_de_computacao_cai_em_editora_tecnica():
    """`Refactoring` já apareceu na Editora 34, que é de literatura/humanas."""
    tecnicas = {"Novatec", "Bookman", "Casa do Código", "Artmed"}
    for titulo, autores, _ in OBRAS:
        if categoria_da_obra(titulo, autores) != "computacao":
            continue
        escolhida = editora_para(titulo, autores)
        assert escolhida in tecnicas, f"{titulo}: {escolhida} não é editora técnica"


def test_editoras_de_humanas_nao_sao_tecnicas():
    """Editora 34 e Boitempo não publicam manual de programação.

    A Artmed fica de fora desta checagem: publica medicina e ciência, então
    aparecer em `ciencia` é legítimo.
    """
    so_tecnicas = {"Novatec", "Bookman", "Casa do Código"}
    for categoria, lista in EDITORAS_POR_CATEGORIA.items():
        if categoria in ("computacao", "ciencia"):
            continue
        assert not (set(lista) & so_tecnicas), (
            f"categoria {categoria} inclui editora exclusivamente técnica"
        )


def test_poesia_nao_cai_em_editora_tecnica():
    titulos_poesia = [
        ("Alguma Poesia", ("Carlos Drummond de Andrade",)),
        ("Libertinagem", ("Manuel Bandeira",)),
    ]
    tecnicas = set(EDITORAS_POR_CATEGORIA["computacao"])
    for titulo, autores in titulos_poesia:
        assert editora_para(titulo, autores) not in tecnicas


# --- coerência do acervo ----------------------------------------------------


def test_titulos_sao_unicos():
    """O seed usa o título como chave estável da editora."""
    duplicados = {t: n for t, n in Counter(t for t, _, _ in OBRAS).items() if n > 1}
    assert not duplicados, f"títulos repetidos: {duplicados}"


def test_toda_obra_tem_autor():
    sem_autor = [titulo for titulo, autores, _ in OBRAS if not autores]
    assert not sem_autor, f"obras sem autor: {sem_autor}"


def test_ano_plausivel():
    for titulo, _, ano in OBRAS:
        assert 1400 <= ano <= 2100, f"{titulo}: ano {ano}"
