# Conexão somente-leitura a bancos reais

O Chat SQL passa a aceitar uma **Conexão** a um banco de dados real, desde que estritamente somente-leitura. Isso substitui o ADR 0001 ("nunca se conecta a um banco real"), porque instituições querem consultar os seus próprios dados sem exportar planilhas. A garantia de segurança deixa de ser "nunca tocar um banco" e passa a ser em camadas: (1) o usuário da Instituição deve ser **read-only**; (2) a sessão é aberta em modo leitura; (3) a Trava continua bloqueando DDL/DML; (4) limites de tempo, linhas e tabelas permitidas.

## Consequences

- Uma Conexão passa a ser mais uma Fonte de Dados, ao lado de Planilha e Script SQL.
- Exige um novo módulo `chat_sql/db.py` (A IMPLEMENTAR pelo grupo) e um ADR de segurança quando o conector existir.
- Erros de permissão e rede passam a ser parte do Diagnóstico.
- O modo em memória (planilhas/DDL) continua sendo o caminho de demonstração sem instalação.
