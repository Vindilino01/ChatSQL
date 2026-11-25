"""Mede a bateria cega: perguntas escritas por quem não viu o motor.

Diferente de `tests/eval/test_acuracia.py` (conjuntos escritos por quem ajustou
o motor), esta bateria é coletada do grupo. O script:

1. lê `tests/eval/bateria_cega.txt` (uma pergunta por linha, `#` é comentário);
2. gera o SQL com o Motor Offline e executa no banco real;
3. imprime pergunta, SQL e resultado para **conferência humana**.

Por que não medir sozinho: sem um SQL de referência escrito à mão, não há como
afirmar "acertou". O que o script garante é que a pergunta virou SQL e que o
SQL rodou; se a resposta está certa é julgamento de quem conhece a biblioteca.

Uso:
    .\\venv\\Scripts\\python scripts\\medir_bateria_cega.py

Devolve código 1 quando o arquivo ainda não tem perguntas — para o comando não
passar por engano num pipeline.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chat_sql.db import DatabaseConfig, DatabaseSource  # noqa: E402
from chat_sql.offline import OfflineEngine  # noqa: E402

ARQUIVO = ROOT / "tests" / "eval" / "bateria_cega.txt"


def ler_perguntas(caminho: Path = ARQUIVO) -> list[str]:
    """Perguntas do arquivo, ignorando comentários e linhas vazias."""
    if not caminho.exists():
        return []
    perguntas = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        limpa = linha.strip()
        if not limpa or limpa.startswith("#"):
            continue
        perguntas.append(limpa)
    return perguntas


def main() -> int:
    perguntas = ler_perguntas()
    if not perguntas:
        print(f"Nenhuma pergunta em {ARQUIVO.relative_to(ROOT)}.")
        print("Cole as perguntas do grupo no arquivo (veja o cabeçalho dele).")
        return 1

    load_dotenv(ROOT / ".env")
    url = os.getenv("CHATSQL_SEED_URL")
    if not url:
        print("ERRO: defina CHATSQL_SEED_URL no .env (precisa do banco real).")
        return 1

    url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    source = DatabaseSource(DatabaseConfig(url=url))
    engine = OfflineEngine(dialect="postgres")

    com_sql = 0
    com_resultado = 0
    try:
        for numero, pergunta in enumerate(perguntas, 1):
            print(f"\n{numero}. {pergunta}")
            sql = engine.generate_sql(pergunta, source.schema)
            if not sql:
                motivo = getattr(engine, "last_reason", "") or "não entendeu"
                print(f"   SEM SQL: {motivo}")
                continue
            com_sql += 1
            print(f"   SQL: {sql}")
            try:
                resultado = source.execute(sql)
            except Exception as exc:  # noqa: BLE001 - queremos seguir para a próxima
                print(f"   ERRO ao executar: {str(exc)[:120]}")
                continue
            com_resultado += 1
            linhas = resultado.rows[:5]
            print(f"   {len(resultado.rows)} linha(s); primeiras: {linhas}")

        print("\n" + "=" * 60)
        print(f"{len(perguntas)} perguntas")
        print(f"{com_sql} viraram SQL ({com_sql / len(perguntas):.0%})")
        print(f"{com_resultado} executaram sem erro")
        print("\nConfira à mão se a resposta faz sentido para a biblioteca.")
        print("Só depois registre o número em docs/AVALIACAO-MOTOR.md.")
    finally:
        source.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
