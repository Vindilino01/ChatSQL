"""Gera docs/mer/biblioteca.drawio a partir do banco real.

O draw.io abre o arquivo direto (File -> Open). Assim o grupo não precisa
montar o diagrama à mão nem depender de importação de Mermaid.

Uso:
    .\\venv\\Scripts\\python scripts/exportar_drawio.py

Cada tabela vira uma caixa com cabeçalho, colunas e marcas PK/FK/NN. As FKs
viram setas com cardinalidade 1:N (notação pé-de-galinha).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chat_sql.db import DatabaseConfig, DatabaseSource  # noqa: E402

OUT = ROOT / "docs" / "mer" / "biblioteca.drawio"

# Layout: três colunas de caixas. Ajuste fino para o diagrama não embolar.
POSICOES = {
    "usuario": (40, 40),
    "emprestimo": (420, 40),
    "exemplar": (800, 40),
    "livro": (800, 320),
    "livro_autor": (1180, 320),
    "autor": (1180, 560),
    "editora": (420, 320),
}

LARGURA = 300
ALTURA_CABECALHO = 30
ALTURA_LINHA = 22
COR_CABECALHO = "#1F3864"
COR_CORPO = "#DAE8FC"
COR_BORDA = "#1F3864"


# Nomes de exibição com acentuação correta (o nome técnico fica no DDL).
NOMES_EXIBICAO = {
    "emprestimo": "EMPRÉSTIMO",
    "usuario": "USUÁRIO",
    "autor": "AUTOR",
    "editora": "EDITORA",
    "livro": "LIVRO",
    "exemplar": "EXEMPLAR",
    "livro_autor": "LIVRO_AUTOR",
}

# Rótulos legíveis das colunas no diagrama.
COLUNAS_EXIBICAO = {
    "pais": "país",
    "codigo_patrimonio": "código de patrimônio",
    "estado_conservacao": "estado de conservação",
    "ano_publicacao": "ano de publicação",
    "data_emprestimo": "data do empréstimo",
    "data_prevista_devolucao": "data prevista de devolução",
    "data_devolucao": "data de devolução",
    "data_cadastro": "data de cadastro",
    "tipo_usuario": "tipo de usuário",
}


def _xml_id(prefixo: str, nome: str) -> str:
    return f"{prefixo}_{nome}"


def _rotulo_coluna(coluna, pks: set[str], fks: set[str]) -> str:
    """Texto de uma linha da tabela, com as marcas entre colchetes.

    Uma coluna pode ser PK e FK ao mesmo tempo — é o caso das tabelas de
    ligação (`livro_autor`), onde a chave é composta por duas FKs.
    """
    nome = coluna.name.lower()
    marcas = []
    if nome in pks:
        marcas.append("PK")
    if nome in fks:
        marcas.append("FK")
    if not coluna.not_null and nome not in pks:
        marcas.append("(nulo)")
    tipo = {"INTEGER": "bigint", "REAL": "numeric", "TEXT": "varchar", "DATE": "date",
            "TIMESTAMP": "timestamptz", "BOOLEAN": "boolean", "BLOB": "bytea"}.get(coluna.type, coluna.type.lower())
    exibicao = COLUNAS_EXIBICAO.get(nome, coluna.name)
    marca = f"  [{', '.join(marcas)}]" if marcas else ""
    return f"{exibicao}: {tipo}{marca}"


def _fracao_da_coluna(tabela, nome: str, altura: float) -> float:
    """Posição vertical (0 a 1) do centro de uma coluna dentro da caixa.

    Usada para ancorar a seta na altura da coluna que ela representa — sem
    isso a linha sai do meio da tabela e parece vir da coluna errada.
    """
    nomes = [coluna.name.lower() for coluna in tabela.columns]
    try:
        indice = nomes.index(nome.lower())
    except ValueError:
        return 0.5
    if altura <= 0:
        return 0.5
    centro = ALTURA_CABECALHO + indice * ALTURA_LINHA + ALTURA_LINHA / 2
    # O centro de uma linha fica sempre dentro da caixa (o menor caso é
    # 0,79 para uma tabela de uma coluna e o maior 0,93 para seis). O limite
    # só protege contra geometria estranha — apertá-lo desalinharia a seta
    # da linha que ela representa.
    return round(min(0.95, max(0.05, centro / altura)), 3)


def _ancoras(origem: tuple[float, float, float, float],
             destino: tuple[float, float, float, float],
             fracao_origem: float,
             fracao_destino: float) -> tuple[float, float, float, float]:
    """Escolhe em que lado de cada caixa a seta encosta.

    Compara os centros: a seta sai pelo lado voltado para o alvo. Ancorar no
    centro (`0.5, 0.5`) fazia a linha atravessar a própria tabela e cobrir o
    texto — o draw.io desenha as arestas por cima dos vértices.
    """
    ox, oy, largura_o, altura_o = origem
    dx, dy, largura_d, altura_d = destino
    delta_x = (dx + largura_d / 2) - (ox + largura_o / 2)
    delta_y = (dy + altura_d / 2) - (oy + altura_o / 2)

    if abs(delta_x) >= abs(delta_y):
        # Lado a lado: sai pela direita ou pela esquerda, na altura da coluna.
        if delta_x >= 0:
            return 1.0, fracao_origem, 0.0, fracao_destino
        return 0.0, fracao_origem, 1.0, fracao_destino
    # Empilhadas: sai por baixo ou por cima, no meio da largura.
    if delta_y >= 0:
        return 0.5, 1.0, 0.5, 0.0
    return 0.5, 0.0, 0.5, 1.0


def _geometria(tabelas) -> dict[str, tuple[float, float, float, float]]:
    """x, y, largura e altura de cada caixa, na ordem em que serão desenhadas."""
    caixas: dict[str, tuple[float, float, float, float]] = {}
    for indice, tabela in enumerate(tabelas):
        padrao = (40 + (indice % 3) * 380, 40 + (indice // 3) * 280)
        x, y = POSICOES.get(tabela.name.lower(), padrao)
        altura = ALTURA_CABECALHO + ALTURA_LINHA * len(tabela.columns)
        caixas[tabela.name.lower()] = (x, y, LARGURA, altura)
    return caixas


def gerar_xml(schema) -> str:
    tabelas = list(schema.tables.values())
    caixas = _geometria(tabelas)

    # Vértices primeiro, arestas depois: no draw.io o que vem por último é
    # desenhado por cima. Assim uma linha nunca cobre o texto de uma tabela.
    vertices: list[str] = []
    arestas: list[str] = []

    for tabela in tabelas:
        x, y, _, altura = caixas[tabela.name.lower()]
        pks = {nome.lower() for nome in tabela.primary_keys}
        fks = {coluna.lower() for fk in tabela.foreign_keys for coluna in fk.columns}

        # Caixa que agrupa cabeçalho + colunas
        vertices.append(
            f'<mxCell id="{_xml_id("box", tabela.name)}" value="" '
            f'style="rounded=0;whiteSpace=wrap;html=1;fillColor={COR_CORPO};'
            f'strokeColor={COR_BORDA};verticalAlign=top;align=left;spacingLeft=6;spacingTop=4;" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{LARGURA}" height="{altura}" as="geometry"/>'
            f"</mxCell>"
        )

        # Cabeçalho com o nome da tabela
        vertices.append(
            f'<mxCell id="{_xml_id("hdr", tabela.name)}" '
            f'value="{escape(NOMES_EXIBICAO.get(tabela.name.lower(), tabela.name.upper()))}" '
            f'style="rounded=0;whiteSpace=wrap;html=1;fillColor={COR_CABECALHO};'
            f'fontColor=#FFFFFF;fontStyle=1;strokeColor={COR_BORDA};align=center;'
            f'verticalAlign=middle;fontSize=13;" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{LARGURA}" height="{ALTURA_CABECALHO}" as="geometry"/>'
            f"</mxCell>"
        )

        # Colunas
        for linha, coluna in enumerate(tabela.columns):
            texto = _rotulo_coluna(coluna, pks, fks)
            destaque = "fontStyle=1;" if coluna.name.lower() in pks else ""
            vertices.append(
                f'<mxCell id="{_xml_id("col_" + coluna.name, tabela.name)}" '
                f'value="{escape(texto)}" '
                f'style="text;html=1;align=left;verticalAlign=middle;spacingLeft=8;'
                f'fontSize=11;{destaque}" vertex="1" parent="1">'
                f'<mxGeometry x="{x}" y="{y + ALTURA_CABECALHO + linha * ALTURA_LINHA}" '
                f'width="{LARGURA}" height="{ALTURA_LINHA}" as="geometry"/>'
                f"</mxCell>"
            )

    # FKs como setas com cardinalidade, desenhadas do lado "muitos" (a tabela
    # que tem a FK) para o lado "um" (a tabela referenciada). É a direção da
    # leitura de um MER: `emprestimo` (N) -> `usuario` (1).
    for tabela in tabelas:
        origem_box = caixas[tabela.name.lower()]
        for fk in tabela.foreign_keys:
            alvo = schema.tables.get(fk.ref_table.lower())
            if alvo is None:
                continue
            if not fk.columns:
                continue

            destino_box = caixas[alvo.name.lower()]
            saida_y = _fracao_da_coluna(tabela, fk.columns[0], origem_box[3])
            # Aponta para a coluna referenciada; sem ela, para a PK do alvo.
            referencia = fk.ref_columns[0] if fk.ref_columns else (alvo.primary_keys or [""])[0]
            entrada_y = _fracao_da_coluna(alvo, referencia, destino_box[3])
            exit_x, exit_y, entry_x, entry_y = _ancoras(
                origem_box, destino_box, saida_y, entrada_y
            )

            # `startArrow` é o lado de `source` — a tabela com a FK. Por isso
            # o "muitos" (ERmany) fica no início e o "um" (ERone) no fim.
            arestas.append(
                f'<mxCell id="{_xml_id("fk", tabela.name + "_" + fk.columns[0])}" value="1:N" '
                f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;'
                f"exitX={exit_x};exitY={exit_y};entryX={entry_x};entryY={entry_y};"
                f'startArrow=ERmany;startFill=0;endArrow=ERone;endFill=0;'
                f'strokeColor=#666666;fontSize=9;" '
                f'edge="1" parent="1" source="{_xml_id("box", tabela.name)}" '
                f'target="{_xml_id("box", alvo.name)}">'
                f'<mxGeometry relative="1" as="geometry"/>'
                f"</mxCell>"
            )

    corpo = "\n        ".join(vertices + arestas)
    return (
        '<mxfile host="app.diagrams.net" type="device">\n'
        '  <diagram id="biblioteca" name="Biblioteca Universitária">\n'
        '    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        'pageWidth="1600" pageHeight="1100" math="0" shadow="0">\n'
        "      <root>\n"
        '        <mxCell id="0"/>\n'
        '        <mxCell id="1" parent="0"/>\n'
        f"        {corpo}\n"
        "      </root>\n"
        "    </mxGraphModel>\n"
        "  </diagram>\n"
        "</mxfile>\n"
    )


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.getenv("CHATSQL_SEED_URL")
    if not url:
        print("ERRO: defina CHATSQL_SEED_URL no .env")
        return 1

    source = DatabaseSource(
        DatabaseConfig(url=url.replace("postgresql://", "postgresql+psycopg://", 1))
    )
    xml = gerar_xml(source.schema)
    source.close()

    OUT.write_text(xml, encoding="utf-8")
    print(f"gerado: {OUT.relative_to(ROOT)} ({len(xml)} bytes)")
    print(f"tabelas: {len(source.schema.tables)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
