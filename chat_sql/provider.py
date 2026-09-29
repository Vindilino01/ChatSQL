"""Cliente de Provedor OpenAI-compatible.

Cobre DeepSeek, OpenAI, Groq, OpenRouter, Together e servidores locais. A chave
vive apenas na sessao do usuario; nada e persistido aqui.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from .config import DEFAULT_TEMPERATURE, REQUEST_TIMEOUT_SECONDS


class ProviderError(Exception):
    """Erro generico do Provedor."""


class AuthError(ProviderError):
    """Chave invalida ou acesso negado."""


class RateLimitError(ProviderError):
    """Limite de requisicoes atingido."""


class NetworkError(ProviderError):
    """Falha de rede ou timeout."""


class LLMProvider(Protocol):
    def generate(self, messages: Sequence[dict], *, temperature: float = ...) -> str: ...

    def test_connection(self) -> None: ...


def _translate(exc: Exception) -> ProviderError:
    try:
        import openai
    except ImportError:
        return ProviderError(str(exc))
    if isinstance(exc, openai.AuthenticationError):
        return AuthError("Chave de API invalida ou nao autorizada.")
    if isinstance(exc, openai.PermissionDeniedError):
        return AuthError("Acesso negado pelo Provedor.")
    if isinstance(exc, openai.RateLimitError):
        return RateLimitError("Limite de requisicoes atingido. Tente novamente em instantes.")
    if isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError)):
        return NetworkError("Nao foi possivel conectar ao Provedor (rede ou timeout).")
    return ProviderError(str(exc))


class OpenAICompatibleProvider:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ProviderError("Pacote 'openai' nao instalado.") from exc
            self._client = OpenAI(
                api_key=self.api_key or "not-needed",
                base_url=self.base_url,
                timeout=self.timeout,
            )
        return self._client

    def generate(
        self,
        messages: Sequence[dict],
        *,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=list(messages),
                temperature=temperature,
            )
        except Exception as exc:
            raise _translate(exc) from exc
        if not response.choices:
            raise ProviderError("O Provedor nao retornou nenhuma resposta.")
        return response.choices[0].message.content or ""

    def test_connection(self) -> None:
        self.generate(
            [{"role": "user", "content": "Responda apenas com a palavra: ok"}],
            temperature=0.0,
        )
