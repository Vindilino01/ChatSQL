"""Terceiro conjunto: linguagem coloquial, como um funcionário falaria de verdade.

Nenhuma destas perguntas foi usada para ajustar o motor. Se a acurácia aqui for
boa, o ganho é generalizável, não sobreajuste.
"""

from __future__ import annotations

# (pergunta, SQL de referência)
COLOQUIAL: list[tuple[str, str]] = [
    # jeito de falar de balcão
    (
        "ô, me vê quantos livro tem aí",
        "SELECT COUNT(*) FROM livro",
    ),
    (
        "rapaz, quantos usuário nós tem",
        "SELECT COUNT(*) FROM usuario",
    ),
    (
        "me passa a lista dos autor",
        "SELECT DISTINCT nome FROM autor",
    ),
    (
        "queria os livro que saíram esse ano",
        "SELECT titulo FROM livro WHERE ano_publicacao = 2026",
    ),
    (
        "tem livro de 1999?",
        "SELECT titulo FROM livro WHERE ano_publicacao = 1999",
    ),
    # abreviações
    (
        "qtd de exemplares",
        "SELECT COUNT(*) FROM exemplar",
    ),
    (
        "qtos emprestimos ativos",
        "SELECT COUNT(*) FROM emprestimo WHERE data_devolucao IS NULL",
    ),
    # perguntas com nome próprio
    (
        "cadê os livro do Saramago",
        "SELECT titulo FROM livro WHERE titulo ILIKE '%saramago%'",
    ),
    (
        "tem Ensaio sobre a Cegueira?",
        "SELECT titulo FROM livro WHERE titulo ILIKE '%ensaio sobre a cegueira%'",
    ),
    # filtros compostos
    (
        "livro publicado entre 1990 e 2000",
        "SELECT titulo FROM livro WHERE ano_publicacao BETWEEN 1990 AND 2000",
    ),
    # agrupamento
    (
        "me faz um resumo de quantos livro por editora",
        "SELECT editora.nome, COUNT(*) FROM livro JOIN editora "
        "ON editora.id_editora = livro.id_editora GROUP BY editora.nome",
    ),
    # ordenação
    (
        "os livro mais velho da biblioteca",
        "SELECT ano_publicacao FROM livro ORDER BY ano_publicacao ASC LIMIT 1",
    ),
    # data relativa
    (
        "quanto emprestimo rolou no mes passado",
        "SELECT COUNT(*) FROM emprestimo WHERE data_emprestimo >= (CURRENT_DATE - INTERVAL '1 months')",
    ),
    # nulo
    (
        "tem usuario sem email?",
        "SELECT nome FROM usuario WHERE email IS NULL",
    ),
    # domínio
    (
        "quantos aluno matriculado",
        "SELECT COUNT(*) FROM usuario WHERE tipo_usuario = 'aluno'",
    ),
    # mistura de domínios
    (
        "quantos exemplar tá em manutenção",
        "SELECT COUNT(*) FROM exemplar WHERE estado_conservacao = 'em_manutencao'",
    ),
    # pergunta ampla
    (
        "me mostra tudo de livro",
        "SELECT titulo FROM livro",
    ),
    # fora do domínio — deve recusar
    (
        "qual a capital da frança",
        "__RECUSAR__",
    ),
]
