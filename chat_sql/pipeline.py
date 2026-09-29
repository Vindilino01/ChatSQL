"""Orquestracao: gerar -> Trava -> (confirmar) -> executar -> Correcao.

A geracao e a validacao acontecem ao enviar a Pergunta. A execucao so ocorre
por confirmacao explicita do usuario. Se a execucao falhar, a Consulta
corrigida volta para a tela e exige novo clique (ver ADR 0004).
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import MAX_ATTEMPTS
from .engine import InMemoryDatabase, QueryError, QueryResult
from .guard import clean_sql, validate
from .prompt import build_messages, execution_feedback, validation_feedback
from .provider import LLMProvider
from .schema import Schema


@dataclass
class Proposal:
    sql: str
    attempts_used: int


@dataclass
class RunOutcome:
    status: str  # "ok" | "corrected" | "failed"
    result: QueryResult | None = None
    proposal: Proposal | None = None
    error: str | None = None
    attempts_used: int = 0


class ChatSession:
    def __init__(
        self,
        provider: LLMProvider,
        schema: Schema,
        database: InMemoryDatabase,
        fewshots: list[tuple[str, str]],
    ) -> None:
        self.provider = provider
        self.schema = schema
        self.database = database
        self.fewshots = fewshots
        self.messages: list[dict] = []
        self.attempts_used = 0
        self.last_error: str | None = None
        self.last_result = None

    def start_question(self, question: str) -> Proposal | None:
        if getattr(self.provider, "offline", False):
            return self._start_offline(question)
        self.messages = build_messages(self.schema, self.fewshots, question)
        self.attempts_used = 0
        self.last_error = None
        return self._propose()

    def _start_offline(self, question: str) -> Proposal | None:
        self.messages = []
        self.attempts_used = 0
        self.last_error = None
        sql = self.provider.generate_sql(question, self.schema)
        self.last_result = getattr(self.provider, "last_result", None)
        self.attempts_used = 1
        if not sql:
            self.last_error = getattr(self.provider, "last_reason", "") or "Nao entendi a pergunta."
            return None
        outcome = validate(sql, self.schema)
        if outcome.ok and outcome.sql:
            return Proposal(sql=outcome.sql, attempts_used=1)
        self.last_error = outcome.error
        return None

    def _propose(self) -> Proposal | None:
        while self.attempts_used < MAX_ATTEMPTS:
            raw = self.provider.generate(self.messages)
            self.attempts_used += 1
            sql = clean_sql(raw)
            outcome = validate(sql, self.schema)
            if outcome.ok and outcome.sql:
                return Proposal(sql=outcome.sql, attempts_used=self.attempts_used)
            self.last_error = outcome.error
            self.messages.append({"role": "assistant", "content": raw or sql})
            self.messages.append(
                {"role": "user", "content": validation_feedback(outcome.error or "Consulta invalida.")}
            )
        return None

    def run(self, proposal: Proposal) -> RunOutcome:
        try:
            result = self.database.execute(proposal.sql)
            return RunOutcome(status="ok", result=result, attempts_used=self.attempts_used)
        except QueryError as exc:
            self.last_error = str(exc)
            if self.attempts_used >= MAX_ATTEMPTS:
                return RunOutcome(status="failed", error=str(exc), attempts_used=self.attempts_used)
            self.messages.append({"role": "assistant", "content": proposal.sql})
            self.messages.append({"role": "user", "content": execution_feedback(str(exc))})
            corrected = self._propose()
            if corrected is not None:
                return RunOutcome(status="corrected", proposal=corrected, attempts_used=self.attempts_used)
            return RunOutcome(status="failed", error=self.last_error, attempts_used=self.attempts_used)

    @property
    def attempts_remaining(self) -> int:
        return max(0, MAX_ATTEMPTS - self.attempts_used)
