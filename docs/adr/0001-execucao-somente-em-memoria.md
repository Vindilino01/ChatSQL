# Execução somente em memória, com dados sintéticos

> **Status:** substituído pelo [ADR 0008](0008-conexao-somente-leitura.md), que passou a permitir Conexões somente-leitura a bancos reais.

O Chat SQL nunca se conecta a um banco de dados real. O usuário fornece apenas o Schema da Sessão (DDL) e o app gera Dados de Exemplo em um SQLite em memória, descartado ao fim da sessão. Decidimos isso para que a Trava (somente leitura) seja uma garantia real de segurança: não há dado de produção a vazar nem banco real a corromper, e o demo permanece auto-contido. A alternativa — conectar a um arquivo `.db` ou banco real do usuário — foi rejeitada por ampliar a superfície de risco sem ganho para o público-alvo.

## Consequences

- O app não serve para consultar dados reais; os Resultados são ilustrativos.
- Toda tabela precisa de Dados de Exemplo para produzir resultados não vazios.
