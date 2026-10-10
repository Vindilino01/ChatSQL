# Fontes e Histórico persistidos em disco

[Início](../../README.md) · [Índice](../README.md) · [Todas as decisões](.)

As Fontes de Dados são salvas em `~/.chat_sql_sources/<hash>/` e o Histórico (Perguntas, Consultas e Resultados já executados) fica junto. A fonte ativa é lembrada na URL (`?src=<hash>`), então recarregar a página restaura tudo automaticamente. Decidimos persistir porque `st.session_state` morre a cada reload e obrigar o usuário a reenviar a planilha é atrito inaceitável. As alternativas consideradas foram manter tudo apenas em memória (perde no reload) e um banco de sessões (complexidade desnecessária para uso local).

## Consequências

- Os dados ficam gravados localmente em disco; a aba Configurações expõe "Limpar fontes salvas".
- Reenviar o mesmo arquivo reutiliza a mesma Fonte Salva (hash do conteúdo).
- O Histórico guarda Resultados; para planilhas grandes isso pode ocupar espaço, mas fica limitado às últimas perguntas.
