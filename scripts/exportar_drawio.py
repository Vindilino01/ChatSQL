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


def _rotulo_coluna(coluna, pks: set[str]) -> str:
    marcas = []
    if coluna.name in pks:
        marcas.append("PK")
    elif coluna.name.lower().endswith("_id"):
        marcas.append("FK")
    if not coluna.not_null and coluna.name not in pks:
        marcas.append("(nulo)")
    tipo = {"INTEGER": "bigint", "REAL": "numeric", "TEXT": "varchar", "DATE": "date",
            "TIMESTAMP": "timestamptz", "BOOLEAN": "boolean", "BLOB": "bytea"}.get(coluna.type, coluna.type.lower())
    nome = COLUNAS_EXIBICAO.get(coluna.name.lower(), coluna.name)
    marca = f"  [{', '.join(marcas)}]" if marcas else ""
    return f"{nome}: {tipo}{marca}"


def gerar_xml(schema) -> str:
    celulas: list[str] = []
    tabelas = list(schema.tables.values())

    for indice, tabela in enumerate(tabelas):
        x, y = POSICOES.get(tabela.name.lower(), (40 + (indice % 3) * 380, 40 + (indice // 3) * 280))
        pks = set(tabela.primary_keys)
        altura = ALTURA_CABECALHO + ALTURA_LINHA * len(tabela.columns)

        # Caixa que agrupa cabeçalho + colunas
        celulas.append(
            f'<mxCell id="{_xml_id("box", tabela.name)}" value="" '
            f'style="rounded=0;whiteSpace=wrap;html=1;fillColor={COR_CORPO};'
            f'strokeColor={COR_BORDA};verticalAlign=top;align=left;spacingLeft=6;spacingTop=4;" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{LARGURA}" height="{altura}" as="geometry"/>'
            f"</mxCell>"
        )

        # Cabeçalho com o nome da tabela
        celulas.append(
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
            texto = _rotulo_coluna(coluna, pks)
            destaque = "fontStyle=1;" if coluna.name in pks else ""
            celulas.append(
                f'<mxCell id="{_xml_id("col_" + coluna.name, tabela.name)}" '
                f'value="{escape(texto)}" '
                f'style="text;html=1;align=left;verticalAlign=middle;spacingLeft=8;'
                f'fontSize=11;{destaque}" vertex="1" parent="1">'
                f'<mxGeometry x="{x}" y="{y + ALTURA_CABECALHO + linha * ALTURA_LINHA}" '
                f'width="{LARGURA}" height="{ALTURA_LINHA}" as="geometry"/>'
                f"</mxCell>"
            )

    # FKs como setas com cardinalidade
    for tabela in tabelas:
        for fk in tabela.foreign_keys:
            origem = _xml_id("box", tabela.name)
            destino = _xml_id("box", fk.ref_table)
            if fk.ref_table.lower() not in schema.tables:
                continue
            celulas.append(
                f'<mxCell id="{_xml_id("fk", tabela.name + "_" + fk.columns[0])}" value="1:N" '
                f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;'
                f'exitX=0.5;exitY=0.5;entryX=0.5;entryY=0.5;startArrow=ERone;'
                f'startFill=0;endArrow=ERmany;endFill=0;strokeColor=#666666;fontSize=9;" '
                f'edge="1" parent="1" source="{origem}" target="{destino}">'
                f'<mxGeometry relative="1" as="geometry"/>'
                f"</mxCell>"
            )

    corpo = "\n        ".join(celulas)
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
