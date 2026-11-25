"""Bateria cega com gabarito: pergunta -> SQL que responde de verdade.

Escrito olhando o dicionário de dados (não o código do motor). A comparação é
por **resultado**: o SQL do motor precisa devolver o mesmo conjunto que o SQL
de referência. Isso pega o caso perigoso — SQL que roda mas não filtra nada.
"""

from __future__ import annotations

# (pergunta, SQL de referência, categoria)
CASOS: list[tuple[str, str, str]] = [
    # ---------------- contagem ----------------
    (
        "quantos livros a gente tem cadastrado",
        "SELECT COUNT(*) FROM livro",
        "contagem",
    ),
    (
        "me diz quantos autores estão cadastrados",
        "SELECT COUNT(*) FROM autor",
        "contagem",
    ),
    (
        "qual o número de usuários",
        "SELECT COUNT(*) FROM usuario",
        "contagem",
    ),
    (
        "quantos exemplares no total",
        "SELECT COUNT(*) FROM exemplar",
        "contagem",
    ),
    (
        "quantas editoras temos",
        "SELECT COUNT(*) FROM editora",
        "contagem",
    ),
    (
        "quantos empréstimos já foram feitos",
        "SELECT COUNT(*) FROM emprestimo",
        "contagem",
    ),
    # ---------------- contagem com filtro ----------------
    (
        "quantos empréstimos ainda não foram devolvidos",
        "SELECT COUNT(*) FROM emprestimo WHERE data_devolucao IS NULL",
        "contagem+filtro",
    ),
    (
        "quantos usuários são alunos",
        "SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'aluno'",
        "contagem+filtro",
    ),
    (
        "quantos exemplares estão danificados",
        "SELECT COUNT(*) FROM exemplar WHERE estado_conservacao = 'danificado'",
        "contagem+filtro",
    ),
    (
        "quantos livros foram publicados depois de 2000",
        "SELECT COUNT(*) FROM livro WHERE ano_publicacao > 2000",
        "contagem+filtro",
    ),
    # ---------------- agrupamento ----------------
    (
        "quantos livros por editora",
        "SELECT editora.nome, COUNT(*) FROM livro JOIN editora "
        "ON editora.id_editora = livro.id_editora GROUP BY editora.nome",
        "agrupamento",
    ),
    (
        "quantos usuários por tipo",
        "SELECT tipo_usuario, COUNT(*) FROM usuario GROUP BY tipo_usuario",
        "agrupamento",
    ),
    (
        "quantos exemplares por estado de conservação",
        "SELECT estado_conservacao, COUNT(*) FROM exemplar GROUP BY estado_conservacao",
        "agrupamento",
    ),
    (
        "quantidade de empréstimos por mês",
        "SELECT to_char(data_emprestimo,'YYYY-MM'), COUNT(*) FROM emprestimo "
        "GROUP BY to_char(data_emprestimo,'YYYY-MM')",
        "agrupamento",
    ),
    # ---------------- listagem ----------------
    (
        "quais são os autores cadastrados",
        "SELECT DISTINCT nome FROM autor",
        "listagem",
    ),
    (
        "listar as editoras",
        "SELECT DISTINCT nome FROM editora",
        "listagem",
    ),
    # ---------------- ranking ----------------
    (
        "quais os 10 livros mais antigos",
        "SELECT ano_publicacao FROM livro ORDER BY ano_publicacao ASC LIMIT 10",
        "ranking",
    ),
    (
        "os 5 livros mais recentes",
        "SELECT ano_publicacao FROM livro ORDER BY ano_publicacao DESC LIMIT 5",
        "ranking",
    ),
    (
        "quais os 20 empréstimos mais recentes",
        "SELECT data_emprestimo FROM emprestimo ORDER BY data_emprestimo DESC LIMIT 20",
        "ranking",
    ),
    # ---------------- busca por texto ----------------
    (
        "tem algum livro com Dom Casmurro no título",
        "SELECT titulo FROM livro WHERE titulo ILIKE '%dom casmurro%'",
        "texto",
    ),
    (
        "quantos livros com Machado",
        "SELECT COUNT(*) FROM livro WHERE titulo ILIKE '%machado%'",
        "texto",
    ),
    # ---------------- filtro numérico ----------------
    (
        "livros publicados antes de 1950",
        "SELECT titulo FROM livro WHERE ano_publicacao < 1950",
        "numerico",
    ),
    (
        "livros com ano de publicação maior que 2010",
        "SELECT titulo FROM livro WHERE ano_publicacao > 2010",
        "numerico",
    ),
    # ---------------- datas ----------------
    (
        "quantos empréstimos no mês passado",
        "SELECT COUNT(*) FROM emprestimo "
        "WHERE data_emprestimo >= (CURRENT_DATE - INTERVAL '1 months')",
        "data",
    ),
    (
        "quantos empréstimos este ano",
        "SELECT COUNT(*) FROM emprestimo WHERE data_emprestimo >= date_trunc('year', CURRENT_DATE)",
        "data",
    ),
    (
        "quantos usuários cadastrados nos últimos 30 dias",
        "SELECT COUNT(*) FROM usuario WHERE data_cadastro >= (CURRENT_DATE - INTERVAL '30 days')",
        "data",
    ),
    # ---------------- nulos ----------------
    (
        "quais usuários não têm email cadastrado",
        "SELECT nome FROM usuario WHERE email IS NULL",
        "nulo",
    ),
    (
        "tem algum empréstimo sem data de devolução",
        "SELECT id_usuario FROM emprestimo WHERE data_devolucao IS NULL",
        "nulo",
    ),
]

# Perguntas que NÃO devem gerar SQL.
NAO_DEVEM_RESPONDER = [
    "qual a previsão do tempo para amanhã",
    "me conta uma piada",
    "quem ganhou a copa do mundo de 2002",
]
