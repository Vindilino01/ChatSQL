"""Conjunto de validação: perguntas escritas DEPOIS do motor, nunca usadas para ajustá-lo.

Este é o teste honesto. Se a acurácia aqui for alta, o ganho é real; se for
baixa, o 100% da bateria de desenvolvimento foi sobreajuste.
"""

from __future__ import annotations

# (pergunta, SQL de referência) — escritas variando vocabulário e sintaxe.
VALIDACAO: list[tuple[str, str]] = [
    # contagens com vocabulário diferente
    (
        "me fala quantos livros estão no acervo",
        "SELECT COUNT(*) FROM livro",
    ),
    (
        "gostaria de saber o total de usuários cadastrados",
        "SELECT COUNT(*) FROM usuario",
    ),
    (
        "existem quantos exemplares",
        "SELECT COUNT(*) FROM exemplar",
    ),
    (
        "número total de empréstimos registrados",
        "SELECT COUNT(*) FROM emprestimo",
    ),
    # filtros por domínio com outra sintaxe
    (
        "quero saber quantos professores temos",
        "SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'professor'",
    ),
    (
        "quantos funcionários estão cadastrados",
        "SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'funcionario'",
    ),
    (
        "tem quantos exemplares em manutenção",
        "SELECT COUNT(*) FROM exemplar WHERE estado_conservacao = 'em_manutencao'",
    ),
    # agrupamentos
    (
        "distribuição de livros por editora",
        "SELECT editora.nome, COUNT(*) FROM livro JOIN editora "
        "ON editora.id_editora = livro.id_editora GROUP BY editora.nome",
    ),
    (
        "quantos livros cada autor escreveu",
        "SELECT a.nome, COUNT(*) FROM livro_autor la "
        "JOIN autor a ON a.id_autor = la.id_autor GROUP BY a.nome",
    ),
    # listagens
    (
        "me lista os títulos dos livros",
        "SELECT DISTINCT titulo FROM livro",
    ),
    (
        "quero ver os nomes dos usuários",
        "SELECT nome FROM usuario",
    ),
    # ranking com outra redação
    (
        "os 15 livros mais novos do acervo",
        "SELECT ano_publicacao FROM livro ORDER BY ano_publicacao DESC LIMIT 15",
    ),
    (
        "me mostra os 7 empréstimos mais antigos",
        "SELECT data_emprestimo FROM emprestimo ORDER BY data_emprestimo ASC LIMIT 7",
    ),
    # busca textual
    (
        "tem algum livro chamado Torto Arado",
        "SELECT titulo FROM livro WHERE titulo ILIKE '%torto arado%'",
    ),
    (
        "procuro livros da autora Clarice",
        "SELECT titulo FROM livro WHERE titulo ILIKE '%clarice%'",
    ),
    # filtros numéricos
    (
        "livros com publicação anterior a 1900",
        "SELECT titulo FROM livro WHERE ano_publicacao < 1900",
    ),
    (
        "quais livros foram publicados em 2019",
        "SELECT titulo FROM livro WHERE ano_publicacao = 2019",
    ),
    # datas
    (
        "empréstimos realizados nos últimos 7 dias",
        "SELECT data_emprestimo FROM emprestimo WHERE data_emprestimo >= (CURRENT_DATE - INTERVAL '7 days')",
    ),
    (
        "quantos empréstimos foram feitos no mês atual",
        "SELECT COUNT(*) FROM emprestimo WHERE data_emprestimo >= date_trunc('month', CURRENT_DATE)",
    ),
    # nulos com outra redação
    (
        "livros que não têm cadastro de editora",
        "SELECT titulo FROM livro WHERE id_editora IS NULL",
    ),
]
