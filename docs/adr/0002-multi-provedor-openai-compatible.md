# Multi-provedor via API OpenAI-compatible com chave do usuário

O Chat SQL fala um único protocolo OpenAI-compatible (`base_url` + `model` + `api_key`), o que cobre DeepSeek, OpenAI, Groq, OpenRouter, Together e servidores locais como Ollama e LM Studio. A chave é fornecida pelo usuário na interface e mantida apenas em `st.session_state`, nunca persistida em disco nem registrada em log. A alternativa — fixar um único provedor (ex.: DeepSeek) — foi rejeitada para atender ao requisito de "o modelo que ele quiser". Anthropic fica como adapter opcional, por falar outro protocolo.

## Consequences

- Recursos específicos de cada provedor não são aproveitados.
- O padrão do autor usa DeepSeek; o usuário final traz a própria chave.
