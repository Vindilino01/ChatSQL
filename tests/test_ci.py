"""O CI precisa estar correto — um workflow inválido só falha depois do push.

Sem estes testes, um erro de indentação no YAML fica invisível até o primeiro
build vermelho no GitHub, e o portfólio mostra um check quebrado.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="instale requirements-dev.txt")

RAIZ = Path(__file__).resolve().parents[1]
WORKFLOWS = RAIZ / ".github" / "workflows"


def _workflows() -> list[Path]:
    if not WORKFLOWS.exists():
        return []
    return sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))


def test_existe_ao_menos_um_workflow():
    assert _workflows(), "nenhum workflow em .github/workflows/"


@pytest.mark.parametrize("arquivo", _workflows(), ids=lambda p: p.name)
def test_yaml_e_valido(arquivo):
    dados = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    assert isinstance(dados, dict), f"{arquivo.name} não é um mapeamento YAML"


@pytest.mark.parametrize("arquivo", _workflows(), ids=lambda p: p.name)
def test_tem_jobs_com_passos(arquivo):
    dados = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    jobs = dados.get("jobs")
    assert jobs, f"{arquivo.name} não define jobs"
    for nome, job in jobs.items():
        passos = job.get("steps")
        assert passos, f"job {nome!r} não tem steps"
        assert job.get("runs-on"), f"job {nome!r} não declara runs-on"
        for passo in passos:
            assert "run" in passo or "uses" in passo, (
                f"passo em {nome!r} sem run nem uses: {passo}"
            )


def test_ci_nao_depende_de_credencial():
    """O CI público não pode falhar por falta de secret.

    O job principal força CHATSQL_SEED_URL vazio para os testes de banco se
    pularem. Se alguém exigir a variável, o build quebra num fork.
    """
    dados = yaml.safe_load((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
    principal = dados["jobs"]["testes"]
    ambiente = {
        chave: valor
        for passo in principal["steps"]
        for chave, valor in (passo.get("env") or {}).items()
    }
    assert ambiente.get("CHATSQL_SEED_URL") == "", (
        "o job principal precisa forçar CHATSQL_SEED_URL vazio"
    )


def test_ci_roda_lint_e_testes():
    dados = yaml.safe_load((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
    comandos = " ".join(
        passo.get("run", "")
        for job in dados["jobs"].values()
        for passo in job.get("steps", [])
    )
    assert "pyflakes" in comandos, "o CI não roda lint"
    assert "pytest" in comandos, "o CI não roda testes"
