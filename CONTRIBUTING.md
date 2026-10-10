# Como contribuir

Guia rápido para o grupo (7 pessoas). A ideia é que qualquer pessoa consiga rodar,
entender e evoluir o projeto sem quebrar o que já funciona.

> **Está em qual frente?** Comece pelo guia dela em [`docs/frentes/`](docs/frentes/).
> Se você nunca programou, veja primeiro [`docs/COMECE-AQUI.md`](docs/COMECE-AQUI.md).

[Início](README.md) · [Índice da documentação](docs/README.md) · [Mapa: onde fica o quê](docs/ONDE-FICA-O-QUE.md)

---

## 1. Preparar o ambiente

```bash
git clone <url-do-repo>
cd ChatSQL
python -m venv venv
.\venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
pytest
```

Se tudo passar (133 testes + 6 guias `skip`), você está pronto.

## 2. Fluxo de trabalho

1. Atualize a `main`: `git pull`.
2. Crie um branch: `git checkout -b frente-a/conector-sqlite`.
3. Faça mudanças pequenas e commits claros.
4. Rode `pytest` antes de abrir o Pull Request.
5. Abra o PR explicando **o que** e **por quê**; peça review de outra pessoa.
6. Só faça merge com a suíte verde.

## 3. Testes

- Todo comportamento novo precisa de teste.
- Os arquivos `tests/test_*.py` funcionam como **especificação**: leia antes de implementar.
- Testes marcados com `@pytest.mark.skip` são **guias** das features do roadmap.
  Ao implementar, remova o `skip`.
- Rode um teste só: `pytest tests/test_db_connector.py -v`.

## 4. Estilo

- Docstrings em português explicando **o que** o módulo faz e **por quê**.
- Nomes de funções/variáveis claros; evite abreviações.
- Nada de `print`; use mensagens na tela.
- Uma responsabilidade por arquivo (veja `docs/ARQUITETURA.md`).

## 5. Receitas

### Adicionar um sinônimo ao Motor Offline

1. Abra `chat_sql/nl/lexicon.py`.
2. Se for uma unidade ("anos" -> idade), adicione em `SEMANTIC_HINTS`.
3. Se for um valor de medida ("faturamento" -> valor_total), ajuste `MEASURE_KEYWORDS`.
4. Rode `pytest tests/test_offline_extended.py -v`.

### Adicionar um novo padrão de pergunta

1. Entenda o fluxo em `chat_sql/nl/engine.py` (`_detect_aggregation`, `_extract_*`).
2. Escreva o teste primeiro (em `tests/`).
3. Implemente o mínimo para passar.
4. Atualize o `README.md` (seção "O que o Motor Offline entende").

### Adicionar uma nova Fonte de Dados (ex.: banco real)

1. Leia `chat_sql/datasource.py` (a interface).
2. Implemente `schema()` e `execute()`.
3. Ligue na tela (`app.py`) como uma nova opção na aba Dados.
4. Ative os testes-guia correspondentes.

## 6. Decisões (ADRs)

Decisões importantes viram um arquivo em `docs/adr/`, no formato `NNNN-titulo.md`, com
1-3 frases (contexto, decisão, por quê). Numere seguindo o último existente.
Exemplos: por que conexão read-only (0008), por que motor offline (0005).

## 7. Definição de pronto

- [ ] `pytest` verde.
- [ ] Teste cobrindo o comportamento novo.
- [ ] Comentário docstring onde a lógica não for óbvia.
- [ ] `ROADMAP.md` atualizado (tarefa marcada).
- [ ] PR revisado por outra pessoa.

---

[Início](README.md) · [Índice da documentação](docs/README.md) · [Guia da sua frente](docs/frentes/)
