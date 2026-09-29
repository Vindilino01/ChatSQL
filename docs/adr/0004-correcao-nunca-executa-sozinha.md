# Correção de Consulta nunca executa sem nova confirmação

Quando uma Consulta falha na execução, o Chat SQL devolve o erro ao modelo e gera uma nova Consulta, mas **não** a executa automaticamente: ela reaparece na tela e exige um novo clique em Executar. A confirmação humana antes da execução é o que sustenta a confiança no app — o usuário sempre vê o SQL que roda em seu nome. A alternativa — auto-executar a Consulta corrigida dentro do loop — foi rejeitada justamente porque tiraria do usuário a chance de inspecionar o que foi corrigido. O orçamento de três SQLs é compartilhado entre validação e execução.

## Consequences

- O fluxo tem mais cliques em caso de erro, de propósito.
- Um leitor futuro pode achar que "faltou" auto-executar a correção; é deliberado.
