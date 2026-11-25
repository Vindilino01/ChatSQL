# Postgres, Neon e o dialeto do Motor Offline

[Início](../../README.md) · [Índice](../README.md) · [Todas as decisões](.)

A demonstração usa um Postgres hospedado no **Neon**, e o schema da biblioteca vive em `public` (ver [BANCO.md](../BANCO.md)). Isso obrigou duas decisões que não estavam previstas quando o projeto começou:

1. **O Motor Offline passou a falar dialetos.** Ele gerava SQL exclusivo de SQLite (`date('now')`, `strftime`), que não existe no Postgres. Criamos `chat_sql/nl/dialect.py` para que a mesma pergunta produza SQL válido em cada banco. A alternativa — reescrever o motor para um dialeto só — foi rejeitada porque o modo em memória continua sendo o caminho de demonstração sem instalação.

2. **A conexão é somente leitura em três camadas.** Usuário read-only no banco, `SET TRANSACTION READ ONLY` na conexão e a Trava bloqueando qualquer coisa que não seja `SELECT`.

## Consequências

- Todo padrão novo do motor precisa de teste nos dois dialetos (`tests/test_dialect.py`).
- Um banco novo (MySQL, SQL Server) exige apenas uma nova subclasse em `dialect.py`.
- O host gratuito escolhido não pausa por inatividade, o que evita chegar na apresentação com o banco suspenso.
