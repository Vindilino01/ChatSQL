"""Configuracao central: presets de Provedor e limites do app."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPreset:
    label: str
    base_url: str
    default_model: str
    requires_key: bool = True


PROVIDER_PRESETS: dict[str, ProviderPreset] = {
    "DeepSeek": ProviderPreset("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat"),
    "OpenAI": ProviderPreset("OpenAI", "https://api.openai.com/v1", "gpt-4o"),
    "Groq": ProviderPreset("Groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "OpenRouter": ProviderPreset("OpenRouter", "https://openrouter.ai/api/v1", "openai/gpt-4o"),
    "Together": ProviderPreset("Together", "https://api.together.xyz/v1", "meta-llama/Llama-3.3-70B-Instruct-Turbo"),
    "Ollama (local)": ProviderPreset("Ollama", "http://localhost:11434/v1", "llama3.1", requires_key=False),
    "LM Studio (local)": ProviderPreset("LM Studio", "http://localhost:1234/v1", "local-model", requires_key=False),
}

OFFLINE_PROVIDER = "Modo offline (sem IA)"

# Offline e o padrao; a IA e a ultima alternativa (opcional, com chave).
DEFAULT_PROVIDER = OFFLINE_PROVIDER

# Orcamento de Tentativas: 1 geracao inicial + 2 Correcoes.
MAX_ATTEMPTS = 3

# Parametros de geracao.
DEFAULT_TEMPERATURE = 0.0
REQUEST_TIMEOUT_SECONDS = 60.0

# Dados de Exemplo.
SAMPLE_ROWS_DEFAULT = 50
SAMPLE_ROWS_MIN = 10
SAMPLE_ROWS_MAX = 500

# Limites de execucao.
MAX_FETCH_ROWS = 1000
DISPLAY_ROWS = 200
QUERY_TIMEOUT_SECONDS = 5.0

# Pares de Exemplos gerados por schema.
FEWSHOT_MIN = 3
FEWSHOT_MAX = 5
