"""Popula o banco da biblioteca com dados fictícios sobre um acervo real.

Obras, autores e editoras são reais (ver scripts/acervo_biblioteca.py). Os
ISBNs são sintéticos (válidos no dígito verificador) e exemplares, usuários e
empréstimos são gerados.

Uso:
    .\\venv\\Scripts\\python scripts\\seed_biblioteca.py [--usuarios N]

Requisitos do schema respeitados (ver schemas/biblioteca-postgres.sql):
- tipo_usuario em ('aluno', 'professor', 'funcionario')
- estado_conservacao em ('bom', 'danificado', 'em_manutencao', 'extraviado', 'descartado')
- data_prevista_devolucao > data_emprestimo
- no máximo um empréstimo ativo por exemplar
- documento (11 dígitos), email, isbn e codigo_patrimonio únicos
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from acervo_biblioteca import EDITORAS, OBRAS  # noqa: E402

TIPOS_USUARIO = ("aluno", "professor", "funcionario")
ESTADOS = ("bom", "bom", "bom", "bom", "danificado", "em_manutencao", "extraviado", "descartado")
NACIONALIDADES = (
    "Brasil", "Portugal", "Argentina", "Chile", "Colômbia", "México", "Espanha",
    "França", "Itália", "Alemanha", "Reino Unido", "Estados Unidos", "Rússia",
    "Japão", "China", "Nigéria", "Angola", "Moçambique", "Áustria", "Irlanda",
)

# Quantos exemplares cada livro recebe (a maioria tem 1 ou 2).
def _exemplares_por_livro(rng: random.Random) -> int:
    return rng.choices([1, 2, 3, 4], weights=[55, 30, 12, 3])[0]


def _isbn13(rng: random.Random) -> str:
    """Gera um ISBN-13 com dígito verificador válido (prefixo 978)."""
    digits = [9, 7, 8] + [rng.randint(0, 9) for _ in range(9)]
    total = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    check = (10 - total % 10) % 10
    return "".join(str(d) for d in digits) + str(check)


def _cpf(rng: random.Random) -> str:
    """Gera 11 dígitos únicos o suficiente para o seed (não é CPF válido)."""
    return "".join(str(rng.randint(0, 9)) for _ in range(11))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--usuarios", type=int, default=800)
    parser.add_argument("--emprestimos", type=int, default=2500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    url = os.getenv("CHATSQL_SEED_URL")
    if not url:
        print("ERRO: defina CHATSQL_SEED_URL no arquivo .env")
        return 1

    rng = random.Random(args.seed)
    faker = Faker("pt_BR")
    Faker.seed(args.seed)

    hoje = date.today()

    with psycopg.connect(url, connect_timeout=30) as conn:
        conn.execute("SET client_encoding TO 'UTF8'")
        with conn.cursor() as cur:
            print("limpando tabelas...")
            cur.execute(
                "TRUNCATE emprestimo, livro_autor, exemplar, livro, autor, editora, usuario "
                "RESTART IDENTITY CASCADE"
            )

            # ---- editoras ----
            print(f"inserindo {len(EDITORAS)} editoras...")
            editora_ids: list[int] = []
            for nome, pais in EDITORAS:
                cur.execute(
                    "INSERT INTO editora (nome, pais) VALUES (%s, %s) RETURNING id_editora",
                    (nome, pais),
                )
                editora_ids.append(cur.fetchone()[0])

            # ---- autores ----
            nomes_autores = sorted({autor for _, autores, _ in OBRAS for autor in autores})
            print(f"inserindo {len(nomes_autores)} autores...")
            autor_ids: dict[str, int] = {}
            for nome in nomes_autores:
                cur.execute(
                    "INSERT INTO autor (nome, nacionalidade) VALUES (%s, %s) RETURNING id_autor",
                    (nome, rng.choice(NACIONALIDADES)),
                )
                autor_ids[nome] = cur.fetchone()[0]

            # ---- livros ----
            print(f"inserindo {len(OBRAS)} livros...")
            livro_rows: list[tuple[int, int]] = []  # (id_livro, quantidade de exemplares)
            for titulo, autores, ano in OBRAS:
                cur.execute(
                    "INSERT INTO livro (titulo, isbn, ano_publicacao, id_editora) "
                    "VALUES (%s, %s, %s, %s) RETURNING id_livro",
                    (titulo, _isbn13(rng), ano, rng.choice(editora_ids)),
                )
                livro_id = cur.fetchone()[0]
                for autor in autores:
                    cur.execute(
                        "INSERT INTO livro_autor (id_livro, id_autor) VALUES (%s, %s) "
                        "ON CONFLICT DO NOTHING",
                        (livro_id, autor_ids[autor]),
                    )
                livro_rows.append((livro_id, _exemplares_por_livro(rng)))

            # ---- exemplares ----
            total_exemplares = sum(qtd for _, qtd in livro_rows)
            print(f"inserindo {total_exemplares} exemplares...")
            exemplar_ids: list[int] = []
            patrimonio = 1
            for livro_id, quantidade in livro_rows:
                for _ in range(quantidade):
                    cur.execute(
                        "INSERT INTO exemplar (codigo_patrimonio, id_livro, estado_conservacao) "
                        "VALUES (%s, %s, %s) RETURNING id_exemplar",
                        (f"PAT-{patrimonio:06d}", livro_id, rng.choice(ESTADOS)),
                    )
                    exemplar_ids.append(cur.fetchone()[0])
                    patrimonio += 1

            # ---- usuarios ----
            print(f"inserindo {args.usuarios} usuarios...")
            documentos: set[str] = set()
            emails: set[str] = set()
            usuario_ids: list[int] = []
            for i in range(args.usuarios):
                while True:
                    documento = _cpf(rng)
                    if documento not in documentos:
                        documentos.add(documento)
                        break
                email = f"usuario{i + 1}@biblioteca.edu.br"
                while email in emails:
                    email = f"usuario{i + 1}.{rng.randint(1, 999)}@biblioteca.edu.br"
                emails.add(email)
                cadastro = faker.date_time_between(start_date="-4y", end_date="now")
                cur.execute(
                    "INSERT INTO usuario (nome, documento, email, tipo_usuario, data_cadastro) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id_usuario",
                    (
                        faker.name(),
                        documento,
                        email,
                        rng.choices(TIPOS_USUARIO, weights=[80, 12, 8])[0],
                        cadastro,
                    ),
                )
                usuario_ids.append(cur.fetchone()[0])

            # ---- emprestimos ----
            print(f"inserindo {args.emprestimos} emprestimos...")
            ativos: set[int] = set()  # exemplares com emprestimo aberto
            inseridos = 0
            tentativas = 0
            while inseridos < args.emprestimos and tentativas < args.emprestimos * 10:
                tentativas += 1
                exemplar_id = rng.choice(exemplar_ids)
                usuario_id = rng.choice(usuario_ids)

                inicio = hoje - timedelta(days=rng.randint(0, 400))
                prevista = inicio + timedelta(days=rng.randint(7, 30))
                devolvido = rng.random() < 0.78

                if devolvido:
                    devolucao = inicio + timedelta(days=rng.randint(1, 45))
                    if devolucao > hoje:
                        devolucao = hoje
                    if devolucao < inicio:
                        devolucao = inicio
                    data_devolucao = devolucao
                else:
                    if exemplar_id in ativos:
                        continue
                    ativos.add(exemplar_id)
                    data_devolucao = None

                cur.execute(
                    "INSERT INTO emprestimo "
                    "(id_usuario, id_exemplar, data_emprestimo, data_prevista_devolucao, data_devolucao) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (usuario_id, exemplar_id, inicio, prevista, data_devolucao),
                )
                inseridos += 1

            cur.execute("ANALYZE")

        conn.commit()

        with conn.cursor() as cur:
            print("\nresumo:")
            for tabela in ("usuario", "editora", "autor", "livro", "livro_autor", "exemplar", "emprestimo"):
                cur.execute(f"SELECT COUNT(*) FROM {tabela}")
                print(f"  {tabela:<12} {cur.fetchone()[0]:>6}")
            cur.execute("SELECT COUNT(*) FROM emprestimo WHERE data_devolucao IS NULL")
            print(f"  {'ativos':<12} {cur.fetchone()[0]:>6}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
