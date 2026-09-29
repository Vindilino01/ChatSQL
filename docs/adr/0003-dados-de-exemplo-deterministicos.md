# Dados de Exemplo determinísticos em vez de gerados pelo LLM

Os Dados de Exemplo são produzidos por um gerador determinístico com seed fixa, a partir de heurísticas de nome e tipo de coluna e respeitando chaves estrangeiras, em vez de pedir `INSERT`s ao modelo. Motivos: reprodutibilidade, zero custo extra de API e ausência de dados incoerentes. A alternativa — geração via LLM — foi rejeitada e fica apenas como fallback para quando a heurística não conseguir produzir nada.

## Consequences

- Os dados são plausíveis, porém genéricos, e não semanticamente ricos.
- A mesma seed produz sempre o mesmo conjunto de dados, o que facilita testes.
