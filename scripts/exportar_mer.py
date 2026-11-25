"""Extrai a estrutura do banco e gera a documentação em docs/mer/.

Lê o catálogo do PostgreSQL (information_schema + pg_catalog) e escreve:

    07-ddl.sql              DDL reconstruído do banco real
    03-dicionario-dados.md  uma linha por coluna, com tipo e restrições
    02-logico.md            diagrama Mermaid (renderiza no GitHub)
    05-indices.md           índices reais, com destaque no único parcial
    biblioteca.dbml         colar em dbdiagram.io e exportar PNG

Uso:
    .\\venv\\Scripts\\python scripts\\exportar_mer.py

Lê CHATSQL_SEED_URL do .env. Não imprime a senha.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "mer"

SCHEMA = "public"

# Descrição de negócio de cada tabela (o que ela guarda, em linguagem simples).
TABELA_DESCRICAO = {
    "usuario": "Quem pega livros emprestados: alunos, professores e funcionários.",
    "editora": "Empresa que publica o livro.",
    "autor": "Quem escreveu a obra.",
    "livro": "A obra em si — título, ISBN e ano. Não é a cópia física.",
    "exemplar": "A cópia física do livro, com código de patrimônio e estado.",
    "livro_autor": "Liga livros a autores (um livro pode ter vários autores).",
    "emprestimo": "Retirada e devolução de um exemplar por um usuário.",
}

# Descrição de cada coluna, quando o nome não fala por si.
COLUNA_DESCRICAO = {
    ("usuario", "id_usuario"): "Identificador único do usuário.",
    ("usuario", "nome"): "Nome completo.",
    ("usuario", "documento"): "CPF com 11 dígitos, sem pontos nem traço.",
    ("usuario", "email"): "E-mail institucional.",
    ("usuario", "tipo_usuario"): "aluno · professor · funcionario.",
    ("usuario", "data_cadastro"): "Quando o usuário foi cadastrado.",
    ("editora", "id_editora"): "Identificador único da editora.",
    ("editora", "nome"): "Razão social.",
    ("editora", "pais"): "País de origem.",
    ("autor", "id_autor"): "Identificador único do autor.",
    ("autor", "nome"): "Nome do autor.",
    ("autor", "nacionalidade"): "País de origem do autor.",
    ("livro", "id_livro"): "Identificador único da obra.",
    ("livro", "titulo"): "Título da obra.",
    ("livro", "isbn"): "ISBN-13 com 13 dígitos, sem hífens.",
    ("livro", "ano_publicacao"): "Ano da edição, entre 1400 e 2100.",
    ("livro", "id_editora"): "Editora que publicou.",
    ("exemplar", "id_exemplar"): "Identificador único da cópia física.",
    ("exemplar", "codigo_patrimonio"): "Etiqueta de patrimônio colada no livro.",
    ("exemplar", "id_livro"): "Qual obra esta cópia representa.",
    ("exemplar", "estado_conservacao"): "bom · danificado · em_manutencao · extraviado · descartado.",
    ("livro_autor", "id_livro"): "Obra.",
    ("livro_autor", "id_autor"): "Autor da obra.",
    ("emprestimo", "id_emprestimo"): "Identificador único do empréstimo.",
    ("emprestimo", "id_usuario"): "Quem retirou.",
    ("emprestimo", "id_exemplar"): "Qual cópia foi retirada.",
    ("emprestimo", "data_emprestimo"): "Data da retirada.",
    ("emprestimo", "data_prevista_devolucao"): "Prazo combinado (posterior à retirada).",
    ("emprestimo", "data_devolucao"): "Quando devolveu. Vazio = ainda emprestado.",
}

TIPO_PT = {
    "bigint": "inteiro grande",
    "integer": "inteiro",
    "smallint": "inteiro curto",
    "character varying": "texto",
    "text": "texto",
    "date": "data",
    "timestamp with time zone": "data e hora",
    "boolean": "verdadeiro/falso",
    "numeric": "decimal",
    "real": "decimal",
}

# Tipos no formato do Mermaid (não aceita espaço nem parênteses).
TIPO_MERMAID = {
    "bigint": "bigint",
    "integer": "int",
    "smallint": "smallint",
    "character varying": "varchar",
    "text": "text",
    "date": "date",
    "timestamp with time zone": "timestamptz",
    "boolean": "boolean",
    "numeric": "numeric",
    "real": "real",
}


def _tipo_mermaid(data_type: str) -> str:
    return TIPO_MERMAID.get(data_type.lower(), "varchar")


def _tipo_pt(data_type: str, tamanho: int | None) -> str:
    nome = TIPO_PT.get(data_type.lower(), data_type)
    if tamanho:
        return f"{nome} ({tamanho})"
    return nome


def ler_banco(engine):
    """Lê tudo que precisamos do catálogo do PostgreSQL em poucas consultas."""
    with engine.connect() as conn:
        colunas = conn.execute(
            text(
                """
                SELECT c.table_name, c.column_name, c.data_type,
                       c.character_maximum_length AS tamanho,
                       c.is_nullable, c.column_default, c.ordinal_position,
                       c.is_identity, c.identity_generation
                FROM information_schema.columns c
                WHERE c.table_schema = :schema
                ORDER BY c.table_name, c.ordinal_position
                """
            ),
            {"schema": SCHEMA},
        ).fetchall()

        pks = conn.execute(
            text(
                """
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_name = tc.constraint_name
                 AND kcu.table_schema = tc.table_schema
                WHERE tc.table_schema = :schema
                  AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY tc.table_name, kcu.ordinal_position
                """
            ),
            {"schema": SCHEMA},
        ).fetchall()

        fks = conn.execute(
            text(
                """
                SELECT kcu.table_name AS origem,
                       kcu.column_name AS origem_col,
                       ccu.table_name AS destino,
                       ccu.column_name AS destino_col,
                       rc.delete_rule
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_name = tc.constraint_name
                 AND kcu.table_schema = tc.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                 AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints rc
                  ON rc.constraint_name = tc.constraint_name
                WHERE tc.table_schema = :schema
                  AND tc.constraint_type = 'FOREIGN KEY'
                ORDER BY kcu.table_name, kcu.column_name
                """
            ),
            {"schema": SCHEMA},
        ).fetchall()

        uniques = conn.execute(
            text(
                """
                SELECT tc.table_name, kcu.column_name, tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON kcu.constraint_name = tc.constraint_name
                 AND kcu.table_schema = tc.table_schema
                WHERE tc.table_schema = :schema
                  AND tc.constraint_type = 'UNIQUE'
                ORDER BY tc.table_name, kcu.column_name
                """
            ),
            {"schema": SCHEMA},
        ).fetchall()

        checks = conn.execute(
            text(
                """
                SELECT rel.relname AS tabela, con.conname,
                       pg_get_constraintdef(con.oid) AS definicao
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
                WHERE nsp.nspname = :schema AND con.contype = 'c'
                ORDER BY rel.relname, con.conname
                """
            ),
            {"schema": SCHEMA},
        ).fetchall()

        indices = conn.execute(
            text(
                """
                SELECT tablename, indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = :schema
                ORDER BY tablename, indexname
                """
            ),
            {"schema": SCHEMA},
        ).fetchall()

        contagens = {
            row[0]: row[1]
            for row in conn.execute(
                text(
                    """
                    SELECT relname, n_live_tup FROM pg_stat_user_tables
                    WHERE schemaname = :schema
                    """
                ),
                {"schema": SCHEMA},
            ).fetchall()
        }

    return {
        "colunas": colunas,
        "pks": pks,
        "fks": fks,
        "uniques": uniques,
        "checks": checks,
        "indices": indices,
        "contagens": contagens,
    }


def ordenar_por_dependencia(tabelas: list[str], fks) -> list[str]:
    """Ordena as tabelas para que uma FK nunca referencie tabela ainda não criada."""
    referencias: dict[str, set[str]] = {t: set() for t in tabelas}
    for origem, _col, destino, _dcol, _regra in fks:
        if origem in referencias and destino in referencias and origem != destino:
            referencias[origem].add(destino)

    ordenadas: list[str] = []
    visitadas: set[str] = set()
    visitando: set[str] = set()

    def visitar(tabela: str) -> None:
        if tabela in visitadas or tabela in visitando:
            return
        visitando.add(tabela)
        for dependencia in sorted(referencias.get(tabela, set())):
            visitar(dependencia)
        visitando.discard(tabela)
        visitadas.add(tabela)
        ordenadas.append(tabela)

    for tabela in sorted(tabelas):
        visitar(tabela)
    return ordenadas


def gerar_ddl(dados: dict, tabelas: list[str]) -> str:
    """Reconstrói o DDL a partir do catálogo."""
    linhas = [
        "-- ============================================================",
        "-- BANCO DE DADOS: BIBLIOTECA UNIVERSITARIA",
        "-- Gerado automaticamente a partir do banco em uso.",
        "-- Fonte: information_schema / pg_catalog (PostgreSQL).",
        "-- ============================================================",
        "",
        "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
        "",
    ]
    pk_map = {t: [] for t in tabelas}
    for tabela, coluna in dados["pks"]:
        pk_map.setdefault(tabela, []).append(coluna)

    fk_map = {t: [] for t in tabelas}
    for origem, origem_col, destino, destino_col, regra in dados["fks"]:
        fk_map.setdefault(origem, []).append(
            f'    CONSTRAINT fk_{origem}_{origem_col}\n'
            f'        FOREIGN KEY ("{origem_col}") REFERENCES "{destino}" ("{destino_col}")\n'
            f"        ON DELETE {regra},"
        )

    uniq_map = {t: [] for t in tabelas}
    for tabela, coluna, nome in dados["uniques"]:
        uniq_map.setdefault(tabela, []).append(
            f'    CONSTRAINT {nome} UNIQUE ("{coluna}"),'
        )

    check_map = {t: [] for t in tabelas}
    for tabela, nome, definicao in dados["checks"]:
        check_map.setdefault(tabela, []).append(f"    CONSTRAINT {nome} {definicao},")

    for tabela in tabelas:
        cols = [c for c in dados["colunas"] if c[0] == tabela]
        blocos: list[str] = []
        for _t, nome, tipo, tamanho, nullable, default, _pos, ident, ident_gen in cols:
            parte = f'    "{nome}" {tipo.upper()}'
            if tamanho:
                parte = f'    "{nome}" {tipo.upper()}({tamanho})'
            if ident == "YES":
                parte += " GENERATED ALWAYS AS IDENTITY"
            elif default is not None:
                parte += f" DEFAULT {default}"
            if nullable == "NO":
                parte += " NOT NULL"
            blocos.append(parte + ",")

        pks = pk_map.get(tabela, [])
        if pks:
            colunas_pk = ", ".join(f'"{c}"' for c in pks)
            blocos.append(f'    CONSTRAINT pk_{tabela} PRIMARY KEY ({colunas_pk}),')
        blocos.extend(uniq_map.get(tabela, []))
        blocos.extend(check_map.get(tabela, []))
        blocos.extend(fk_map.get(tabela, []))

        corpo = "\n".join(blocos).rstrip(",")
        linhas.append(f'CREATE TABLE "{tabela}" (\n{corpo}\n);')
        linhas.append("")

        for _, indexname, indexdef in dados["indices"]:
            if indexdef.startswith("CREATE INDEX") or indexdef.startswith("CREATE UNIQUE INDEX"):
                continue
        linhas.append("")

    linhas.append("-- Índices")
    for _, _, indexdef in dados["indices"]:
        if not indexdef.startswith("CREATE UNIQUE INDEX") and "PRIMARY KEY" not in indexdef:
            if indexdef.startswith("CREATE INDEX"):
                linhas.append(indexdef + ";")
    linhas.append("")
    linhas.append("-- Índice único parcial: impede dois empréstimos abertos no mesmo exemplar")
    for _, _, indexdef in dados["indices"]:
        if indexdef.startswith("CREATE UNIQUE INDEX") and "WHERE" in indexdef:
            linhas.append(indexdef + ";")

    return "\n".join(linhas) + "\n"


def gerar_dicionario(dados: dict, tabelas: list[str]) -> str:
    linhas = [
        "# Dicionário de dados",
        "",
        "[Início](../../README.md) · [Índice](README.md)",
        "",
        "Uma linha por coluna. Gerado a partir do banco em uso.",
        "",
    ]
    for tabela in tabelas:
        cols = [c for c in dados["colunas"] if c[0] == tabela]
        if not cols:
            continue
        descricao = TABELA_DESCRICAO.get(tabela, "")
        linhas.append(f"## `{tabela}`")
        linhas.append("")
        if descricao:
            linhas.append(descricao)
            linhas.append("")
        linhas.append("| Coluna | Tipo | Obrigatória | Padrão | O que é |")
        linhas.append("|---|---|---|---|---|")
        for _t, nome, tipo, tamanho, nullable, default, _pos, ident, ident_gen in cols:
            obrigatoria = "sim" if nullable == "NO" else "não"
            padrao = "—"
            if default is not None:
                padrao = f"`{default}`"
            explicacao = COLUNA_DESCRICAO.get((tabela, nome), "")
            linhas.append(
                f'| `{nome}` | {_tipo_pt(tipo, tamanho)} | {obrigatoria} | {padrao} | {explicacao} |'
            )
        linhas.append("")
    return "\n".join(linhas)


def gerar_logico(dados: dict, tabelas: list[str]) -> str:
    linhas = [
        "# Diagrama lógico (tabelas e relacionamentos)",
        "",
        "[Início](../../README.md) · [Índice](README.md)",
        "",
        "Este diagrama é renderizado pelo próprio GitHub — não precisa instalar nada.",
        "",
        "```mermaid",
        "erDiagram",
    ]

    for tabela in tabelas:
        cols = [c for c in dados["colunas"] if c[0] == tabela]
        pks = {c for t, c in dados["pks"] if t == tabela}
        linhas.append(f"    {tabela} {{")
        for _t, nome, tipo, tamanho, nullable, default, _pos, ident, ident_gen in cols:
            tipo_mermaid = _tipo_mermaid(tipo)
            chave = " PK" if nome in pks else ""
            linhas.append(f"        {tipo_mermaid} {nome}{chave}")
        linhas.append("    }")

    linhas.append("")
    for origem, origem_col, destino, destino_col, _ in dados["fks"]:
        linhas.append(f'    {destino} ||--o{{ {origem} : "{origem_col}"')

    linhas.append("```")
    linhas.append("")
    linhas.append("## Relacionamentos")
    linhas.append("")
    linhas.append("| De | Para | Coluna | Regra ao apagar |")
    linhas.append("|---|---|---|---|")
    for origem, origem_col, destino, destino_col, regra in dados["fks"]:
        linhas.append(f"| `{origem}` | `{destino}` | `{origem_col}` | {regra} |")
    linhas.append("")
    linhas.append("## Contagem de registros")
    linhas.append("")
    linhas.append("| Tabela | Registros |")
    linhas.append("|---|---|")
    for tabela in tabelas:
        linhas.append(f"| `{tabela}` | {dados['contagens'].get(tabela, 0):,} |".replace(",", "."))
    linhas.append("")
    return "\n".join(linhas)


def gerar_indices(dados: dict) -> str:
    linhas = [
        "# Índices",
        "",
        "[Início](../../README.md) · [Índice](README.md)",
        "",
        "Índices aceleram a busca ao custo de espaço e de escrita mais lenta.",
        "Como este banco é somente leitura para o app, criamos os que ajudam as consultas.",
        "",
        "| Tabela | Índice | Serve para |",
        "|---|---|---|",
    ]
    motivo = {
        "idx_livro_editora": "juntar livro com editora",
        "idx_livro_titulo_trgm": "buscar por trecho no título (`ILIKE '%dom%'`)",
        "idx_exemplar_livro": "juntar exemplar com livro",
        "idx_livro_autor_autor": "buscar livros de um autor",
        "idx_emprestimo_usuario": "histórico de um usuário",
        "idx_emprestimo_exemplar": "histórico de um exemplar",
        "idx_emprestimo_data": "filtrar por data (mês passado, este ano)",
        "idx_exemplar_emprestimo_ativo": "impedir dois empréstimos abertos no mesmo exemplar",
    }
    for tabela, nome, _definicao in dados["indices"]:
        if nome.startswith("pk_") or nome.startswith("uk_"):
            continue
        linhas.append(f"| `{tabela}` | `{nome}` | {motivo.get(nome, '—')} |")

    linhas.append("")
    linhas.append("## O índice único parcial")
    linhas.append("")
    linhas.append("```sql")
    for _, nome, definicao in dados["indices"]:
        if nome == "idx_exemplar_emprestimo_ativo":
            linhas.append(definicao + ";")
    linhas.append("```")
    linhas.append("")
    linhas.append(
        "Este é o índice mais importante do projeto. Ele implementa **no banco** a regra:\n"
        '"um exemplar não pode ter dois empréstimos abertos ao mesmo tempo".\n'
        "A maioria dos sistemas resolve isso no código da aplicação — onde pode ser burlado.\n"
        "Aqui, nem um `INSERT` manual consegue violar a regra."
    )
    linhas.append("")
    return "\n".join(linhas)


def gerar_dbml(dados: dict, tabelas: list[str]) -> str:
    linhas = ["// Biblioteca Universitária — cole em https://dbdiagram.io", ""]
    pks = {t: [] for t in tabelas}
    for tabela, coluna in dados["pks"]:
        pks.setdefault(tabela, []).append(coluna)

    for tabela in tabelas:
        linhas.append(f"Table {tabela} {{")
        for tabela_col, nome, tipo, tamanho, nullable, default, _pos, ident, ident_gen in dados["colunas"]:
            if tabela_col != tabela:
                continue
            tipo_dbml = tipo.lower()
            if tamanho:
                tipo_dbml = f"varchar({tamanho})"
            atributos = []
            if nome in pks[tabela]:
                atributos.append("pk")
            if nullable == "NO" and nome not in pks[tabela]:
                atributos.append("not null")
            for t, c, u in [(x[0], x[1], x[2]) for x in dados["uniques"]]:
                if t == tabela and c == nome:
                    atributos.append("unique")
                    break
            extra = f" [{', '.join(atributos)}]" if atributos else ""
            nota = COLUNA_DESCRICAO.get((tabela, nome), "")
            nota_dbml = f" [note: '{nota}']" if nota else ""
            linhas.append(f"  {nome} {tipo_dbml}{extra}{nota_dbml}")
        linhas.append("}")
        linhas.append("")

    for origem, origem_col, destino, destino_col, _ in dados["fks"]:
        linhas.append(f"Ref: {origem}.{origem_col} > {destino}.{destino_col}")
    return "\n".join(linhas) + "\n"


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.getenv("CHATSQL_SEED_URL")
    if not url:
        print("ERRO: defina CHATSQL_SEED_URL no arquivo .env")
        return 1

    url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(url)
    dados = ler_banco(engine)
    engine.dispose()

    tabelas = sorted({c[0] for c in dados["colunas"]})
    tabelas_ordenadas = ordenar_por_dependencia(tabelas, dados["fks"])
    OUT.mkdir(parents=True, exist_ok=True)

    (OUT / "07-ddl.sql").write_text(gerar_ddl(dados, tabelas_ordenadas), encoding="utf-8")
    (OUT / "03-dicionario-dados.md").write_text(gerar_dicionario(dados, tabelas), encoding="utf-8")
    (OUT / "02-logico.md").write_text(gerar_logico(dados, tabelas), encoding="utf-8")
    (OUT / "05-indices.md").write_text(gerar_indices(dados), encoding="utf-8")
    (OUT / "biblioteca.dbml").write_text(gerar_dbml(dados, tabelas), encoding="utf-8")

    print(f"tabelas: {len(tabelas)} -> {', '.join(tabelas)}")
    print(f"colunas: {len(dados['colunas'])}")
    print(f"FKs: {len(dados['fks'])} | PKs: {len(dados['pks'])} | UNIQUE: {len(dados['uniques'])} | CHECK: {len(dados['checks'])}")
    print(f"indices: {len(dados['indices'])}")
    print(f"\narquivos gerados em {OUT}:")
    for nome in ("07-ddl.sql", "03-dicionario-dados.md", "02-logico.md", "05-indices.md", "biblioteca.dbml"):
        tamanho = (OUT / nome).stat().st_size
        print(f"  {nome:<28} {tamanho:>7} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
