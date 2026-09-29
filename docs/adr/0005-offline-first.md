# Offline-first: Motor Offline por padrão, IA como última alternativa

O Chat SQL gera Consultas com um Motor Offline determinístico (regras em PT-BR) por padrão, sem enviar nada a serviços externos e sem exigir chave. Um Provedor de IA (OpenAI-compatible) é a alternativa opcional, escolhida explicitamente pelo usuário. A motivação é dupla: usuários que não querem ou não podem pagar por tokens, e ambientes corporativos onde modelos de linguagem são proibidos. A alternativa — IA como padrão e regras como fallback — foi rejeitada porque colocaria a dependência externa no caminho crítico.

## Consequences

- O Motor Offline precisa cobrir sozinho os padrões de Pergunta mais comuns; perguntas fora do vocabulário retornam "não entendi".
- A ingestão de Planilhas é o caminho principal de entrada de dados, não um extra.
- O Par de Exemplos e o loop de Correção só existem no caminho com IA.
