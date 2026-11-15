"""Aplica o DDL da biblioteca no banco configurado em CHATSQL_SEED_URL.

Uso:
    .\\venv\\Scripts\\python scripts\\apply_ddl.py

Le a URL do arquivo .env (nunca a imprime) e executa
`schemas/biblioteca-postgres.sql`. Ao final, mostra as tabelas, os indices e
as extensoes para conferencia.

Atencao: este script DROPA as tabelas da biblioteca se elas ja existirem,
para permitir reexecucao durante o desenvolvimento. Nao use em producao.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DDL_PATH = ROOT / "schemas" / "biblioteca-postgres.sql"
TABLES = ("usuario", "editora", "autor", "livro", "exemplar", "livro_autor", "emprestimo")


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.getenv("CHATSQL_SEED_URL")
    if not url:
        print("ERRO: defina CHATSQL_SEED_URL no arquivo .env")
        return 1

    ddl = DDL_PATH.read_text(encoding="utf-8")

    try:
        with psycopg.connect(url, connect_timeout=20) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user, version()")
                database, user, version = cur.fetchone()
                print(f"conectado em '{database}' como '{user}' ({version.split(',')[0]})")

                cur.execute("DROP TABLE IF EXISTS " + ", ".join(TABLES) + " CASCADE")
                print("tabelas antigas removidas (se existiam)")

                cur.execute(ddl)
            conn.commit()
            print("DDL aplicado com sucesso")
    except Exception as exc:  # mensagem curta, sem vazar a URL
        print(f"ERRO ao aplicar o DDL: {type(exc).__name__}: {exc}")
        return 1

    with psycopg.connect(url, connect_timeout=20) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
            tables = [row[0] for row in cur.fetchall()]
            print(f"\ntabelas em public ({len(tables)}):")
            for name in tables:
                print(f"  - {name}")

            cur.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE schemaname = 'public' ORDER BY indexname"
            )
            indexes = [row[0] for row in cur.fetchall()]
            print(f"\nindices ({len(indexes)}):")
            for name in indexes:
                print(f"  - {name}")

            cur.execute("SELECT extname FROM pg_extension ORDER BY extname")
            print("\nextensoes:", ", ".join(row[0] for row in cur.fetchall()))

            cur.execute(
                "SELECT conname FROM pg_constraint "
                "WHERE connamespace = 'public'::regnamespace ORDER BY conname"
            )
            constraints = [row[0] for row in cur.fetchall()]
            print(f"\nrestricoes ({len(constraints)}):")
            for name in constraints:
                print(f"  - {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
