"""A documentação não pode contradizer o banco.

O README já disse 744 exemplares quando o banco tinha 747. Números digitados à
mão envelhecem; este teste confere os que importam e falha com a mensagem do
que corrigir.

Quando o banco não está acessível (CI sem secret, máquina sem `.env`), os
testes que dependem dele são pulados — o restante continua valendo.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from dotenv import load_dotenv

from scripts.contagens import TABELAS, formatar

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(RAIZ / ".env")
URL = os.getenv("CHATSQL_SEED_URL")

precisa_banco = pytest.mark.skipif(
    not URL, reason="defina CHATSQL_SEED_URL para conferir os números"
)


@pytest.fixture(scope="module")
def contagens() -> dict[str, int]:
    from scripts.contagens import contar

    return contar(URL)


def _texto(caminho: str) -> str:
    return (RAIZ / caminho).read_text(encoding="utf-8")


def _linha_da_tabela(texto: str, tabela: str) -> str | None:
    """Valor da coluna 'Registros' na linha da tabela pedida.

    Aceita `` | `livro` | A obra... | 456 | `` e ``| livro | 456 |``; a crase
    opcional é o que fazia o regex não casar com o README real.
    """
    padrao = re.compile(
        rf"^\|\s*`?{re.escape(tabela)}`?\s*\|.*?\|\s*([\d.]+)\s*\|\s*$",
        re.MULTILINE,
    )
    achado = padrao.search(texto)
    return achado.group(1) if achado else None


# --- os arquivos que citam números -----------------------------------------


@precisa_banco
@pytest.mark.parametrize("item", TABELAS, ids=[item.tabela for item in TABELAS])
def test_readme_mostra_a_contagem_real(contagens, item):
    """O README tem uma tabela de registros que precisa bater com o banco."""
    texto = _texto("README.md")
    citado = _linha_da_tabela(texto, item.tabela)
    assert citado is not None, f"README.md não tem a linha da tabela `{item.tabela}`"
    esperado = formatar(contagens[item.tabela])
    assert citado == esperado, (
        f"README.md diz {citado} para `{item.tabela}`, o banco tem {esperado}. "
        "Rode: .\\venv\\Scripts\\python -m scripts.contagens"
    )


@precisa_banco
def test_readme_nao_cita_contagem_de_exemplares_desatualizada(contagens):
    """O caso concreto que aconteceu: 744 versus 747."""
    texto = _texto("README.md")
    real = formatar(contagens["exemplar"])
    # Qualquer número seguido de "exemplares" no texto precisa ser o real.
    for achado in re.findall(r"(\d[\d.]*)\s+exemplares", texto):
        assert achado == real, f"README.md diz {achado} exemplares; o banco tem {real}"


@precisa_banco
def test_total_de_registros_confere(contagens):
    """O README arredonda ("~5.300"); o valor exato também é aceito.

    Não exige o número quebrado: "cerca de 5.300" é leitura melhor que
    "5.301" num texto de apresentação. O que não pode é dizer 4.000.
    """
    texto = _texto("README.md")
    total = sum(contagens.values())
    aceitos = {
        formatar(total),                      # 5.301
        f"{formatar(total)[:3]}00",           # 5.300 (arredondado)
        f"~{formatar(total)[:3]}00",
    }
    assert any(valor in texto for valor in aceitos), (
        f"o README não cita os {formatar(total)} registros do banco "
        f"(nem o arredondado {formatar(total)[:3]}00)"
    )


@precisa_banco
def test_mer_esta_sincronizado_com_o_banco(contagens):
    """`docs/mer/` é gerado do banco; se o banco muda, o MER tem de mudar.

    Sem isto, alguém troca o seed, esquece de rodar `exportar_mer.py` e o
    diagrama que vai para o relatório mostra contagens antigas.
    """
    texto = _texto("docs/mer/02-logico.md")
    for item in TABELAS:
        citado = _linha_da_tabela(texto, item.tabela)
        if citado is None:
            continue
        esperado = formatar(contagens[item.tabela])
        assert citado == esperado, (
            f"docs/mer/02-logico.md diz {citado} para `{item.tabela}`, "
            f"o banco tem {esperado}. Rode: "
            ".\\venv\\Scripts\\python scripts\\exportar_mer.py"
        )


def test_drawio_esta_sincronizado_com_o_schema():
    """O `.drawio` é gerado; precisa refletir o schema atual."""
    from scripts.exportar_drawio import OUT

    assert OUT.exists()
    conteudo = OUT.read_text(encoding="utf-8")
    assert conteudo.count('id="box_') == 7, "o .drawio não tem as 7 tabelas"
    assert conteudo.count('id="fk_') == 6, "o .drawio não tem as 6 FKs"
    # As marcas de FK já foram esquecidas uma vez.
    assert "[FK]" in conteudo
    assert "[PK, FK]" in conteudo


# --- números de teste -------------------------------------------------------


def _testes_declarados() -> int:
    """Conta os testes que a suíte realmente coleta.

    Usa `--collect-only` porque a contagem por `def test_` não enxerga
    parametrização (`@pytest.mark.parametrize`) nem testes gerados.
    """
    import subprocess
    import sys

    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    )
    achado = re.search(r"(\d+)\s+tests? collected", resultado.stdout)
    if achado:
        return int(achado.group(1))
    # Fallback: conta declarações (subestima parametrizados).
    total = 0
    for arquivo in (RAIZ / "tests").rglob("test_*.py"):
        texto = arquivo.read_text(encoding="utf-8")
        if "pytestmark = pytest.mark.skip" in texto:
            continue
        total += len(re.findall(r"^def test_", texto, re.M))
    return total


def test_a_documentacao_diz_o_numero_certo_de_testes():
    """Nenhum arquivo pode citar um número de testes que não existe.

    Número de teste é a métrica mais fácil de auditar num portfólio — e a mais
    fácil de deixar envelhecer (o APRESENTACAO chegou a citar 204 quando a
    suíte já tinha 340). Este teste varre todos os `.md`.
    """
    coletados = _testes_declarados()
    assert coletados > 100, f"coleta suspeita: {coletados} testes"

    # Números de "passando" e "coletados" são ambos verdadeiros.
    aceitos = {coletados, coletados - 2}

    erros: list[str] = []
    for arquivo in list(RAIZ.glob("*.md")) + list((RAIZ / "docs").rglob("*.md")):
        if "venv" in arquivo.parts:
            continue
        texto = arquivo.read_text(encoding="utf-8")
        for achado in re.findall(r"(\d{2,4})\s+testes", texto):
            citado = int(achado)
            if citado not in aceitos and citado > 50:
                erros.append(f"{arquivo.name}: {citado} testes")

    assert not erros, (
        f"a suíte coleta {coletados} testes; estes arquivos citam outro número:\n"
        + "\n".join(erros)
    )

    assert any(
        str(coletados) in (RAIZ / "README.md").read_text(encoding="utf-8")
        for _ in [0]
    ), f"o README precisa citar {coletados}"


def test_total_de_perguntas_avaliadas_confere():
    """O "95 perguntas" do README tem de ser a soma dos conjuntos reais.

    Se alguém acrescentar perguntas ao quarto conjunto e esquecer de atualizar
    o número, o README passa a mentir sobre a cobertura da avaliação.
    """
    from tests.eval.bateria_cega import CASOS, NAO_DEVEM_RESPONDER
    from tests.eval.coloquial import COLOQUIAL
    from tests.eval.quarto_conjunto import QUARTO_CONJUNTO, RECUSAR
    from tests.eval.validacao import VALIDACAO

    conjuntos = {
        "bateria": [(q, r) for q, r, _ in CASOS],
        "validação": VALIDACAO,
        "coloquial": COLOQUIAL,
        "quarto": QUARTO_CONJUNTO,
    }
    total = sum(
        1 for casos in conjuntos.values() for _, ref in casos if ref != "__RECUSAR__"
    )
    # As recusas vivem em duas listas: a marcação __RECUSAR__ dentro dos
    # conjuntos e a lista NAO_DEVEM_RESPONDER da bateria.
    recusas = sum(
        1 for casos in conjuntos.values() for _, ref in casos if ref == "__RECUSAR__"
    ) + len(NAO_DEVEM_RESPONDER) + len(RECUSAR)

    texto = _texto("README.md")
    assert f"{total}/{total}" in texto, (
        f"o README não cita {total}/{total} perguntas avaliadas (soma real)"
    )
    assert f"{recusas}/{recusas}" in texto, (
        f"o README não cita {recusas}/{recusas} recusas (soma real: "
        f"{len(NAO_DEVEM_RESPONDER)} da bateria + {len(RECUSAR)} do quarto conjunto)"
    )


# --- links e arquivos citados ----------------------------------------------


# Arquivos que a documentação cita mas que são produzidos por vocês (print,
# diagrama exportado). Não existem no repositório de propósito: são o que a
# banca pede como imagem. Listá-los aqui é a diferença entre "pendência
# conhecida" e "link quebrado".
GERADOS_PELO_GRUPO = {
    "docs/imagens/diagrama-er.png",
    "docs/imagens/tela-chat.png",
    "docs/imagens/tela-dados.png",
    "docs/imagens/tela-configuracoes.png",
    "docs/imagens/tela-grafico.png",
}


def test_todos_os_arquivos_citados_na_documentacao_existem():
    """Caminhos em crase que parecem arquivo precisam existir."""
    padrao = re.compile(r"`((?:chat_sql|scripts|tests|docs|schemas)/[\w./-]+\.\w+)`")
    faltando: list[str] = []
    for arquivo in list(RAIZ.glob("*.md")) + list((RAIZ / "docs").rglob("*.md")):
        if "venv" in arquivo.parts:
            continue
        for citado in padrao.findall(arquivo.read_text(encoding="utf-8")):
            if citado in GERADOS_PELO_GRUPO:
                continue
            if not (RAIZ / citado).exists():
                faltando.append(f"{arquivo.name}: {citado}")
    assert not faltando, "arquivos citados que não existem:\n" + "\n".join(faltando)


def test_os_arquivos_gerados_tem_instrucoes():
    """Prometer imagem sem dizer como produzi-la é pior que não citar."""
    instrucoes = _texto("docs/imagens/README.md")
    for caminho in GERADOS_PELO_GRUPO:
        nome = Path(caminho).name
        assert nome in instrucoes, f"docs/imagens/README.md não explica {nome}"


def _slug_do_titulo(titulo: str) -> str:
    """Reproduz o slug que o GitHub gera para um título."""
    slug = titulo.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    return re.sub(r"\s+", "-", slug)


def test_ancoras_internas_apontam_para_titulos_reais():
    """`#secao` que não existe é link quebrado silencioso.

    Um emoji no título muda o slug e quebra o link sem ninguém perceber.
    """
    faltando: list[str] = []
    for arquivo in ("README.md", "RELATORIO.md", "PRODUCT.md", "DESIGN.md"):
        caminho = RAIZ / arquivo
        if not caminho.exists():
            continue
        texto = caminho.read_text(encoding="utf-8")
        ancoras = {
            _slug_do_titulo(titulo)
            for titulo in re.findall(r"^#{2,4}\s+(.+)$", texto, re.M)
        }
        for usada in re.findall(r"\]\(#([^)]+)\)", texto):
            if usada not in ancoras:
                faltando.append(f"{arquivo}: #{usada}")
    assert not faltando, "âncoras que não existem:\n" + "\n".join(faltando)
