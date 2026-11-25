"""Testes do gerador do diagrama para draw.io.

Travam os defeitos que já apareceram no arquivo publicado:

1. as colunas de chave estrangeira não eram marcadas como FK (o teste antigo
   procurava `_id` no fim do nome, mas as colunas se chamam `id_usuario`);
2. as setas saíam do centro da caixa e cobriam o texto da própria tabela;
3. as setas eram desenhadas depois dos vértices, então passavam por cima.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from chat_sql.schema import parse_schema
from scripts.exportar_drawio import gerar_xml

# Schema com os nomes reais da biblioteca, incluindo a tabela de ligação N:N
# (duas FKs que também são PK). O DDL de produção usa `~` (regex do Postgres),
# que o sqlglot não lê — por isso o fixture é reduzido, mas fiel nos nomes.
DDL = """
CREATE TABLE autor (
    id_autor INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    nacionalidade TEXT
);
CREATE TABLE editora (
    id_editora INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    pais TEXT NOT NULL
);
CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY,
    nome TEXT NOT NULL
);
CREATE TABLE livro (
    id_livro INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL,
    id_editora INTEGER NOT NULL,
    FOREIGN KEY (id_editora) REFERENCES editora (id_editora)
);
CREATE TABLE livro_autor (
    id_livro INTEGER NOT NULL,
    id_autor INTEGER NOT NULL,
    PRIMARY KEY (id_livro, id_autor),
    FOREIGN KEY (id_livro) REFERENCES livro (id_livro),
    FOREIGN KEY (id_autor) REFERENCES autor (id_autor)
);
CREATE TABLE exemplar (
    id_exemplar INTEGER PRIMARY KEY,
    id_livro INTEGER NOT NULL,
    FOREIGN KEY (id_livro) REFERENCES livro (id_livro)
);
CREATE TABLE emprestimo (
    id_emprestimo INTEGER PRIMARY KEY,
    id_usuario INTEGER NOT NULL,
    id_exemplar INTEGER NOT NULL,
    data_emprestimo DATE NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario),
    FOREIGN KEY (id_exemplar) REFERENCES exemplar (id_exemplar)
);
"""


@pytest.fixture(scope="module")
def xml() -> str:
    return gerar_xml(parse_schema(DDL))


@pytest.fixture(scope="module")
def cells(xml) -> list:
    return ET.fromstring(xml).findall(".//mxCell")


def _valores(cells, prefixo: str) -> list[str]:
    return [
        c.get("value") or ""
        for c in cells
        if (c.get("id") or "").startswith(prefixo)
    ]


def _arestas(cells) -> list:
    return [c for c in cells if c.get("edge") == "1"]


def _propriedade(estilo: str, nome: str) -> float:
    achado = re.search(rf"{nome}=([\d.]+)", estilo)
    assert achado, f"{nome} ausente no estilo: {estilo}"
    return float(achado.group(1))


def test_xml_bem_formado(xml):
    raiz = ET.fromstring(xml)
    assert raiz.tag == "mxfile"
    assert raiz.find(".//mxGraphModel") is not None


def test_uma_caixa_por_tabela(cells):
    caixas = [c for c in cells if (c.get("id") or "").startswith("box_")]
    assert len(caixas) == 7


def _marcas_por_tabela_coluna(cells) -> dict[tuple[str, str], set[str]]:
    """Extrai as marcas de cada linha: {(tabela, coluna): {"PK", "FK", ...}}.

    O id de uma célula de coluna é `col_<coluna>_<tabela>`, e nem sempre dá
    para separar por split — `livro_autor` tem underscore. Por isso o id é
    comparado com os nomes de tabela conhecidos.
    """
    tabelas = [
        (c.get("id") or "")[4:]
        for c in cells
        if (c.get("id") or "").startswith("box_")
    ]
    resultado: dict[tuple[str, str], set[str]] = {}
    for c in cells:
        cid = c.get("id") or ""
        if not cid.startswith("col_"):
            continue
        corpo = cid[4:]
        tabela = max((t for t in tabelas if corpo.endswith("_" + t)), key=len)
        coluna = corpo[: -len(tabela) - 1]
        valor = c.get("value") or ""
        entre_colchetes = re.search(r"\[([^\]]*)\]", valor)
        marcas = (
            {m.strip() for m in entre_colchetes.group(1).split(",")}
            if entre_colchetes
            else set()
        )
        resultado[(tabela, coluna)] = marcas
    return resultado


def test_coluna_de_fk_e_marcada_como_fk(cells):
    """Regressão: `id_usuario` termina em `_usuario`, não em `_id`."""
    marcas = _marcas_por_tabela_coluna(cells)
    esperado = {
        ("emprestimo", "id_usuario"),
        ("emprestimo", "id_exemplar"),
        ("exemplar", "id_livro"),
        ("livro", "id_editora"),
        ("livro_autor", "id_livro"),
        ("livro_autor", "id_autor"),
    }
    for chave in esperado:
        assert "FK" in marcas.get(chave, set()), f"{chave} deveria ter FK: {marcas.get(chave)}"

    # A PK da própria tabela não é FK.
    assert marcas[("autor", "id_autor")] == {"PK"}
    assert marcas[("emprestimo", "id_emprestimo")] == {"PK"}


def test_tabela_de_ligacao_tem_pk_e_fk(cells):
    marcas = _marcas_por_tabela_coluna(cells)
    assert marcas[("livro_autor", "id_livro")] == {"PK", "FK"}
    assert marcas[("livro_autor", "id_autor")] == {"PK", "FK"}


def test_coluna_nula_e_marcada(cells):
    marcas = _marcas_por_tabela_coluna(cells)
    assert "(nulo)" in marcas[("autor", "nacionalidade")]
    assert "(nulo)" not in marcas[("autor", "nome")]


def test_nenhuma_seta_sai_do_centro(cells):
    """Regressão: âncora no centro atravessava a própria tabela."""
    for aresta in _arestas(cells):
        estilo = aresta.get("style") or ""
        saida = (_propriedade(estilo, "exitX"), _propriedade(estilo, "exitY"))
        assert saida != (0.5, 0.5), f"seta ancorada no centro: {estilo}"


def test_setas_encostam_na_borda_das_caixas(cells):
    """Cada ponta tem de estar numa borda (0 ou 1), não no interior."""
    for aresta in _arestas(cells):
        estilo = aresta.get("style") or ""
        ex, ey = _propriedade(estilo, "exitX"), _propriedade(estilo, "exitY")
        nx, ny = _propriedade(estilo, "entryX"), _propriedade(estilo, "entryY")
        horizontal = ex in (0.0, 1.0) and nx in (0.0, 1.0)
        vertical = ey in (0.0, 1.0) and ny in (0.0, 1.0)
        assert horizontal or vertical, f"ponta no interior da caixa: {estilo}"


def test_setas_desenhadas_depois_das_caixas(cells):
    """No draw.io o último é desenhado por cima: aresta depois de vértice."""
    ids = [c.get("id") for c in cells if c.get("id")]
    vertices = [i for i in ids if i.startswith(("box_", "hdr_", "col_"))]
    arestas = [i for i in ids if i.startswith("fk_")]
    assert vertices and arestas
    assert ids.index(vertices[-1]) < ids.index(arestas[0])


def test_toda_seta_aponta_para_caixa_existente(cells):
    ids = {c.get("id") for c in cells}
    for aresta in _arestas(cells):
        assert aresta.get("source") in ids
        assert aresta.get("target") in ids


def test_cardinalidade_muitos_no_lado_da_fk(cells):
    """A ponta "muitos" fica na tabela que tem a FK, não na referenciada."""
    for aresta in _arestas(cells):
        estilo = aresta.get("style") or ""
        assert "startArrow=ERmany" in estilo
        assert "endArrow=ERone" in estilo


def test_seta_aponta_para_a_coluna_referenciada(cells):
    """`emprestimo.id_usuario` deve entrar na altura de `usuario.id_usuario`."""
    caixas = {}
    for c in cells:
        cid = c.get("id") or ""
        if cid.startswith("box_"):
            g = c.find("mxGeometry")
            caixas[cid[4:]] = (float(g.get("y")), float(g.get("height")))

    for aresta in _arestas(cells):
        if aresta.get("source") != "box_emprestimo":
            continue
        if aresta.get("target") != "box_usuario":
            continue
        estilo = aresta.get("style") or ""
        y, altura = caixas["usuario"]
        esperado = y + _propriedade(estilo, "entryY") * altura
        # id_usuario é a 1a coluna: cabeçalho (30) + meia linha (11).
        assert esperado == pytest.approx(y + 41, abs=1.0)
        return
    pytest.fail("seta emprestimo -> usuario não encontrada")


def test_arquivo_publicado_tem_as_mesmas_garantias():
    """O `.drawio` do repositório precisa estar correto, não só o gerador.

    Este teste lê o arquivo que as pessoas abrem no draw.io — se alguém
    corrigir o gerador e esquecer de rodá-lo, o defeito continua publicado.
    As invariantes são estruturais (não dependem do banco), então valem para
    a versão gerada a partir do Neon.
    """
    from pathlib import Path

    publicado = Path(__file__).resolve().parents[1] / "docs" / "mer" / "biblioteca.drawio"
    assert publicado.exists(), "docs/mer/biblioteca.drawio não existe"
    conteudo = ET.fromstring(publicado.read_text(encoding="utf-8"))
    publicado_cells = conteudo.findall(".//mxCell")

    marcas = _marcas_por_tabela_coluna(publicado_cells)
    assert any("FK" in m for m in marcas.values()), "arquivo publicado sem nenhuma FK"
    assert any(m == {"PK", "FK"} for m in marcas.values()), "arquivo publicado sem PK+FK"

    arestas_publicadas = _arestas(publicado_cells)
    assert len(arestas_publicadas) == 6
    for aresta in arestas_publicadas:
        estilo = aresta.get("style") or ""
        assert (_propriedade(estilo, "exitX"), _propriedade(estilo, "exitY")) != (0.5, 0.5)

    ids = [c.get("id") for c in publicado_cells if c.get("id")]
    vertices = [i for i in ids if i.startswith(("box_", "hdr_", "col_"))]
    arestas_ids = [i for i in ids if i.startswith("fk_")]
    assert ids.index(vertices[-1]) < ids.index(arestas_ids[0])
