"""Quarto conjunto: perguntas escritas a partir do dicionário de dados.

Escritas olhando APENAS `docs/mer/03-dicionario-dados.md` e as regras de
negócio do MER conceitual — sem abrir o código do motor. Servem como medição
independente das três anteriores.

Cada item: (pergunta, SQL de referência). A comparação é por resultado.
"""

from __future__ import annotations

QUARTO_CONJUNTO: list[tuple[str, str]] = [
    # --- contagens puras (vocabulário variado) ---
    (
        "qual a quantidade de obras no acervo",
        "SELECT COUNT(*) FROM livro",
    ),
    (
        "existe quantas editoras cadastradas",
        "SELECT COUNT(*) FROM editora",
    ),
    (
        "total de exemplares físicos",
        "SELECT COUNT(*) FROM exemplar",
    ),
    (
        "quantas pessoas estão cadastradas como usuárias",
        "SELECT COUNT(*) FROM usuario",
    ),
    # --- contagem com filtro por domínio ---
    (
        "quantos exemplares estão em manutenção",
        "SELECT COUNT(*) FROM exemplar WHERE estado_conservacao = 'em_manutencao'",
    ),
    (
        "quantos exemplares foram descartados",
        "SELECT COUNT(*) FROM exemplar WHERE estado_conservacao = 'descartado'",
    ),
    (
        "quantos funcionários existem",
        "SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'funcionario'",
    ),
    # --- contagem com filtro numérico ---
    (
        "quantos livros publicados no século 21",
        "SELECT COUNT(*) FROM livro WHERE ano_publicacao >= 2001",
    ),
    (
        "quantos livros são anteriores a 1900",
        "SELECT COUNT(*) FROM livro WHERE ano_publicacao < 1900",
    ),
    # --- agrupamentos ---
    (
        "quantidade de exemplares por estado de conservação",
        "SELECT estado_conservacao, COUNT(*) FROM exemplar GROUP BY estado_conservacao",
    ),
    (
        "quantos usuários de cada tipo",
        "SELECT tipo_usuario, COUNT(*) FROM usuario GROUP BY tipo_usuario",
    ),
    (
        "quantos livros cada nacionalidade de autor tem",
        "SELECT a.nacionalidade, COUNT(*) FROM autor a "
        "JOIN livro_autor la ON la.id_autor = a.id_autor GROUP BY a.nacionalidade",
    ),
    (
        "quantos exemplares existem por livro",
        "SELECT l.titulo, COUNT(*) FROM livro l JOIN exemplar e "
        "ON e.id_livro = l.id_livro GROUP BY l.titulo",
    ),
    # --- filtro por nacionalidade (país e gentílico) ---
    (
        "quantos autores brasileiros existem",
        "SELECT COUNT(*) FROM autor WHERE nacionalidade = 'Brasil'",
    ),
    (
        "quantos autores são de Portugal",
        "SELECT COUNT(*) FROM autor WHERE nacionalidade = 'Portugal'",
    ),
    (
        "liste os autores moçambicanos",
        "SELECT nome FROM autor WHERE nacionalidade = 'Moçambique'",
    ),
    (
        "quantos autores alemães existem",
        "SELECT COUNT(*) FROM autor WHERE nacionalidade = 'Alemanha'",
    ),
    (
        "quantos autores dos Estados Unidos",
        "SELECT COUNT(*) FROM autor WHERE nacionalidade = 'Estados Unidos'",
    ),
    # --- listagens ---
    (
        "liste o nome de todas as editoras",
        "SELECT DISTINCT nome FROM editora",
    ),
    (
        "quais são os títulos cadastrados",
        "SELECT DISTINCT titulo FROM livro",
    ),
    (
        "mostre os nomes dos autores cadastrados",
        "SELECT DISTINCT nome FROM autor",
    ),
    # --- ranking ---
    (
        "os 10 livros mais antigos do acervo",
        "SELECT ano_publicacao FROM livro ORDER BY ano_publicacao ASC LIMIT 10",
    ),
    (
        "os 5 empréstimos mais recentes",
        "SELECT data_emprestimo FROM emprestimo ORDER BY data_emprestimo DESC LIMIT 5",
    ),
    (
        "os 20 livros mais novos",
        "SELECT ano_publicacao FROM livro ORDER BY ano_publicacao DESC LIMIT 20",
    ),
    # --- busca textual ---
    (
        "tem alguma obra de Machado de Assis",
        "SELECT titulo FROM livro WHERE titulo ILIKE '%machado de assis%'",
    ),
    (
        "existe livro com Quincas no título",
        "SELECT COUNT(*) FROM livro WHERE titulo ILIKE '%quincas%'",
    ),
    # --- datas relativas ---
    (
        "quantos empréstimos foram feitos este mês",
        "SELECT COUNT(*) FROM emprestimo WHERE data_emprestimo >= date_trunc('month', CURRENT_DATE)",
    ),
    (
        "quantos usuários se cadastraram nos últimos 90 dias",
        "SELECT COUNT(*) FROM usuario WHERE data_cadastro >= (CURRENT_DATE - INTERVAL '90 days')",
    ),
    # --- nulos ---
    (
        "quais autores não têm nacionalidade informada",
        "SELECT nome FROM autor WHERE nacionalidade IS NULL",
    ),
    (
        "existem empréstimos ainda em aberto",
        "SELECT COUNT(*) FROM emprestimo WHERE data_devolucao IS NULL",
    ),
]

# Perguntas que devem ser recusadas (fora do domínio da biblioteca).
RECUSAR: list[str] = [
    "qual é a cotação do dólar hoje",
    "me indique um filme para assistir",
]
