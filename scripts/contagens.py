"""Números da demonstração, lidos do banco — fonte única para a documentação.

Já aconteceu de o README dizer 744 exemplares, o PRD dizer 744 e o banco ter
747: o seed mudou e alguém esqueceu de atualizar quatro arquivos. Este módulo
lê os números reais e os formata, para que a documentação seja gerada (ou
conferida) em vez de digitada.

Uso para imprimir o bloco que vai para o README/PRD:

    .\\venv\\Scripts\\python -m scripts.contagens

Uso nos testes (sem tocar no banco): `TABELAS` descreve o formato esperado, e
`tests/test_documentacao.py` confere que a doc não contradiz o banco quando ele
está acessível.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Contagem:
    tabela: str
    singular: str
    plural: str


# Ordem em que as tabelas aparecem na documentação.
TABELAS: tuple[Contagem, ...] = (
    Contagem("livro", "obra", "obras"),
    Contagem("autor", "autor", "autores"),
    Contagem("editora", "editora", "editoras"),
    Contagem("livro_autor", "vínculo autor-obra", "vínculos autor-obra"),
    Contagem("exemplar", "exemplar", "exemplares"),
    Contagem("usuario", "usuário", "usuários"),
    Contagem("emprestimo", "empréstimo", "empréstimos"),
)


def contar(url: str | None = None) -> dict[str, int]:
    """Lê a contagem de cada tabela do banco da demonstração."""
    import psycopg

    if url is None:
        from dotenv import load_dotenv

        load_dotenv()
        url = os.getenv("CHATSQL_SEED_URL")
    if not url:
        raise RuntimeError("defina CHATSQL_SEED_URL no .env")

    with psycopg.connect(url, connect_timeout=30) as conn:
        with conn.cursor() as cur:
            resultado = {}
            for item in TABELAS:
                cur.execute(f"SELECT COUNT(*) FROM {item.tabela}")
                resultado[item.tabela] = cur.fetchone()[0]
    return resultado


def formatar(total: int) -> str:
    """1234 -> '1.234' (padrão brasileiro)."""
    return f"{total:,}".replace(",", ".")


def resumo(contagens: dict[str, int]) -> str:
    """Bloco pronto para colar na documentação."""
    linhas = ["| Tabela | Registros |", "|---|---|"]
    total = 0
    for item in TABELAS:
        n = contagens[item.tabela]
        total += n
        linhas.append(f"| `{item.tabela}` | {formatar(n)} |")
    linhas.append(f"| **Total** | **{formatar(total)}** |")
    return "\n".join(linhas)


def main() -> int:
    contagens = contar()
    print(resumo(contagens))
    print()
    for item in TABELAS:
        n = contagens[item.tabela]
        print(f"{formatar(n):>6} {item.plural if n != 1 else item.singular}")
    print(f"{formatar(sum(contagens.values())):>6} registros no total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
