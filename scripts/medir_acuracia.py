"""Mede a acurácia real: compara o RESULTADO do motor com o de referência.

Um SQL que roda mas devolve tudo (sem filtro) conta como ERRO — é o caso mais
perigoso, porque parece funcionar.

Uso:
    .\\venv\\Scripts\\python scripts/medir_acuracia.py [-v]
"""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chat_sql.db import DatabaseConfig, DatabaseSource  # noqa: E402
from chat_sql.offline import OfflineEngine  # noqa: E402
from tests.eval.bateria_cega import CASOS, NAO_DEVEM_RESPONDER  # noqa: E402

VERBOSE = "-v" in sys.argv


def _resultado(source: DatabaseSource, sql: str) -> list[tuple] | None:
    try:
        return sorted(tuple(r) for r in source.execute(sql).rows)
    except Exception:
        return None


def main() -> int:
    load_dotenv(ROOT / ".env")
    url = os.getenv("CHATSQL_SEED_URL")
    if not url:
        print("ERRO: defina CHATSQL_SEED_URL no .env")
        return 1

    source = DatabaseSource(
        DatabaseConfig(url=url.replace("postgresql://", "postgresql+psycopg://", 1))
    )
    engine = OfflineEngine(dialect=source.dialect)

    por_categoria: dict[str, Counter] = {}
    falhas: list[str] = []

    for pergunta, referencia, categoria in CASOS:
        esperado = _resultado(source, referencia)
        sql = engine.generate_sql(pergunta, source.schema)

        if not sql:
            marca, detalhe = "🚫", engine.last_reason[:60]
        elif esperado is None:
            marca, detalhe = "??", "SQL de referência falhou"
        else:
            obtido = _resultado(source, sql)
            if obtido is None:
                marca, detalhe = "❌", "erro ao executar"
            elif obtido == esperado:
                marca, detalhe = "✅", f"{len(obtido)} linhas"
            else:
                marca, detalhe = "❌", f"esperado {esperado[:2]}... obtido {obtido[:2]}..."

        por_categoria.setdefault(categoria, Counter())[marca] += 1
        if marca != "✅":
            falhas.append(f"  {marca} [{categoria}] {pergunta}\n      motivos: {detalhe}\n      gerado:  {sql}")
        if VERBOSE:
            print(f"{marca} [{categoria:<16}] {pergunta}")
            if sql:
                print(f"      {sql[:120]}")

    print("\n=== POR CATEGORIA ===")
    total_ok = total = 0
    for categoria in sorted(por_categoria):
        c = por_categoria[categoria]
        n = sum(c.values())
        ok = c.get("✅", 0)
        total_ok += ok
        total += n
        barra = "█" * ok + "·" * (n - ok)
        print(f"  {categoria:<16} {barra} {ok}/{n}")

    print(f"\nACURÁCIA: {total_ok}/{total} = {total_ok / total:.0%}")

    # rejeições
    rejeicoes_ok = 0
    for pergunta in NAO_DEVEM_RESPONDER:
        sql = engine.generate_sql(pergunta, source.schema)
        if not sql:
            rejeicoes_ok += 1
        else:
            falhas.append(f"  ⚠️ deveria recusar: {pergunta} -> {sql}")
    print(f"RECUSA CORRETA: {rejeicoes_ok}/{len(NAO_DEVEM_RESPONDER)}")

    if falhas:
        print("\n=== FALHAS ===")
        for f in falhas:
            print(f)

    source.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
