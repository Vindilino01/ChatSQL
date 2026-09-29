from __future__ import annotations


class FakeProvider:
    """Provedor de teste: devolve respostas pre-programadas, sem rede."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list[list[dict]] = []

    def generate(self, messages, *, temperature: float = 0.0) -> str:
        self.calls.append(list(messages))
        if not self.responses:
            raise AssertionError("FakeProvider sem respostas restantes.")
        value = self.responses.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    def test_connection(self) -> None:
        return None
