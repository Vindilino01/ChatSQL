# O Motor Offline nunca falha em silêncio

Quando não consegue mapear uma Pergunta com confiança, o Motor Offline devolve um Diagnóstico estruturado (motivo, tabelas ambíguas e sugestões) em vez de adivinhar ou lançar exceção. A decisão parte do princípio de que uma Consulta errada é pior do que Consulta nenhuma — sobretudo em ambientes corporativos onde a resposta pode embasar decisões. As alternativas consideradas foram "chutar a interpretação mais provável" e "propagar exceções"; a primeira engana o usuário, a segunda derruba o app.

## Consequences

- Perguntas fora do vocabulário terminam em "não entendi" + sugestões, não em SQL plausível porém errado.
- Toda falha interna é capturada e convertida em Diagnóstico; o app não quebra.
- Exige um vocabulário e uma suíte de testes maiores para cobrir os padrões comuns.
