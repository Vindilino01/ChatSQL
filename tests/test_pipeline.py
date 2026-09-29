from __future__ import annotations

import pytest

from chat_sql.pipeline import ChatSession
from chat_sql.provider import AuthError
from tests.helpers import FakeProvider


def make_session(schema, database, responses):
    return ChatSession(FakeProvider(responses), schema, database, [])


def test_valid_on_first_attempt(schema, database):
    session = make_session(schema, database, ["SELECT COUNT(*) FROM clientes;"])
    proposal = session.start_question("Quantos clientes existem?")
    assert proposal is not None
    assert proposal.attempts_used == 1
    assert "COUNT" in proposal.sql.upper()


def test_invalid_then_valid(schema, database):
    session = make_session(
        schema,
        database,
        ["DELETE FROM clientes;", "SELECT COUNT(*) FROM clientes;"],
    )
    proposal = session.start_question("Quantos clientes existem?")
    assert proposal is not None
    assert proposal.attempts_used == 2


def test_budget_exhausted(schema, database):
    session = make_session(schema, database, ["DELETE FROM clientes;"] * 3)
    proposal = session.start_question("Quantos clientes existem?")
    assert proposal is None
    assert session.attempts_used == 3
    assert session.last_error


def test_execution_error_triggers_correction(schema, database):
    session = make_session(
        schema,
        database,
        ["SELECT funcao_inexistente(1);", "SELECT COUNT(*) FROM clientes;"],
    )
    proposal = session.start_question("Quantos clientes existem?")
    outcome = session.run(proposal)
    assert outcome.status == "corrected"
    assert outcome.proposal is not None
    assert "COUNT" in outcome.proposal.sql.upper()
    assert outcome.attempts_used == 2

    final = session.run(outcome.proposal)
    assert final.status == "ok"
    assert final.result.rows[0][0] == 50


def test_corrected_query_is_not_auto_executed(schema, database):
    session = make_session(
        schema,
        database,
        ["SELECT funcao_inexistente(1);", "SELECT COUNT(*) FROM clientes;"],
    )
    proposal = session.start_question("Quantos clientes existem?")
    outcome = session.run(proposal)
    assert outcome.status == "corrected"
    assert outcome.result is None


def test_execution_failure_exhausts_budget(schema, database):
    session = make_session(
        schema,
        database,
        ["SELECT funcao_inexistente(1);"] * 3,
    )
    proposal = session.start_question("q")
    assert proposal.attempts_used == 1
    outcome = session.run(proposal)
    assert outcome.status == "corrected"
    outcome = session.run(outcome.proposal)
    assert outcome.status == "corrected"
    outcome = session.run(outcome.proposal)
    assert outcome.status == "failed"
    assert session.attempts_used == 3


def test_provider_error_does_not_consume_budget(schema, database):
    session = make_session(schema, database, [AuthError("chave invalida")])
    with pytest.raises(AuthError):
        session.start_question("q")
    assert session.attempts_used == 0
