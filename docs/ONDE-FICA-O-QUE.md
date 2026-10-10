# Onde fica o quê

Este arquivo responde à pergunta: **"onde eu mexo para fazer tal coisa?"**

Leia a coluna "O que é isso" sem medo: são explicações simples, sem termo técnico.

[Início](../README.md) · [Índice](README.md) · [Guia da sua frente](../ROADMAP.md)

---

## Mapa rápido

| O que você quer mexer | Onde fica | Quem cuida |
|---|---|---|
| Deixar o robô entender mais perguntas | pasta `chat_sql/nl/` | Frente B |
| Adicionar palavras que ele conhece | `chat_sql/nl/lexicon.py` | Frente B |
| Ligar/desligar a segurança (a Trava) | `chat_sql/guard.py` | Frente B |
| Executar as consultas | `chat_sql/engine.py` (na memória) e `chat_sql/db.py` (banco real) | Frentes A e B |
| Conectar num banco de dados | `chat_sql/db.py` | Frente A |
| As telas (Chat, Dados, Configurações) | `app.py` | Frente C |
| Cores, fontes, cartões, botões (visual) | `app.py` (parte `CSS`, no começo do arquivo) e `.streamlit/config.toml` | Frente C |
| A tabela e o gráfico do resultado | `app.py` (função `_render_result`) | Frente C |
| Dados de exemplo (semente) | `chat_sql/sample_data.py` | Frente D |
| Schemas prontos de demonstração | `schemas/` | Frente D |
| Ler planilhas (CSV, Excel) | `chat_sql/spreadsheet.py` | Frente D |
| Google Sheets e dump `.sql` | `chat_sql/sheets.py` e `chat_sql/sql_dump.py` | Frente D |
| Guardar fontes e histórico | `chat_sql/store.py` | Frente D |
| Publicar / Docker / apresentação | raiz do projeto e `docs/` | Frente E |
| Testes | `tests/` | Todos |

## O que cada pasta e cada arquivo faz

### Na raiz

| Nome | O que é |
|---|---|
| `app.py` | **As telas.** Tudo o que aparece no navegador está aqui. |
| `README.md` | A porta de entrada do projeto no GitHub. |
| `ROADMAP.md` | A lista do que falta fazer, por frente. |
| `PRD.md` | O documento do projeto (visão, arquitetura, resultados). |
| `CONTRIBUTING.md` | Como contribuir e rodar os testes. |
| `CONTEXT.md` | Glossário: o que cada palavra quer dizer. |
| `requirements.txt` | A lista de programas que o projeto precisa para rodar. |

### Pasta `chat_sql/` (o "motor" do projeto)

| Nome | O que é |
|---|---|
| `nl/` | **O cérebro que entende a pergunta** (motor sem IA). |
| `nl/lexicon.py` | As palavras que ele conhece (meses, unidades, sinônimos). |
| `nl/engine.py` | Como ele decide o que a sua pergunta quer. |
| `nl/builder.py` | Como ele monta o SQL final e junta as tabelas. |
| `nl/text.py` | Limpa o texto (acentos, plural). |
| `guard.py` | **A Trava**: só deixa passar consulta de leitura (SELECT). |
| `engine.py` | Roda a consulta na memória (planilhas e exemplos). |
| `db.py` | Conecta num banco de dados de verdade (só leitura). |
| `spreadsheet.py` | Lê planilhas CSV, XLSX e XLS. |
| `store.py` | Guarda as fontes e o histórico no seu computador. |
| `pipeline.py` | Junta tudo: gerar -> validar -> executar. |
| `provider.py` | Fala com a IA (só quando você usa uma chave). |
| `prompt.py` | Monta o texto que vai para a IA. |
| `schema.py` | Entende o `CREATE TABLE` e extrai tabelas e colunas. |
| `sample_data.py` | Cria dados de exemplo para testar. |
| `datasource.py` | A regra que toda Fonte de Dados precisa seguir. |
| `config.py` | Números e padrões do projeto (limites, tempo). |

### Outras pastas

| Nome | O que é |
|---|---|
| `schemas/` | Exemplos de banco prontos (e-commerce, RH, vendas, biblioteca). |
| `exemplos/` | Planilhas de exemplo para testar. |
| `tests/` | Os testes. Também servem de exemplo de como usar o código. |
| `docs/` | Esta documentação e as decisões (ADRs). |
| `docs/imagens/` | Onde colocar os prints das telas. |
| `.github/` | Modelos de tarefa (Issue) e de envio (Pull Request). |

## Se você se perdeu

1. Abra o [COMECE-AQUI.md](COMECE-AQUI.md) para rodar o projeto.
2. Veja a sua frente em [frentes/](frentes/).
3. Se ainda tiver dúvida, pergunte no grupo citando o arquivo (ex.: "estou no `app.py`, linha tal").

---

[Início](../README.md) · [Índice](README.md) · [Guia da sua frente](../ROADMAP.md)
