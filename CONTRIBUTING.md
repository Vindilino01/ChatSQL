# Como contribuir

Guia rapido para o grupo (7 pessoas). A ideia e que qualquer pessoa consiga rodar, entender
e evoluir o projeto sem quebrar o que ja funciona.

## 1. Preparar o ambiente

```bash
git clone <url-do-repo>
cd ChatSQL
python -m venv venv
.\venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
pytest
```

Se tudo passar (133 testes + 6 guias `skip`), voce esta pronto.

## 2. Fluxo de trabalho

1. Atualize a `main`: `git pull`.
2. Crie um branch: `git checkout -b frente-a/conector-sqlite`.
3. Faca mudancas pequenas e commits claros.
4. Rode `pytest` antes de abrir o Pull Request.
5. Abra o PR explicando **o que** e **por que**; peca review de outra pessoa.
6. So faca merge com a suite verde.

## 3. Testes

- Todo comportamento novo precisa de teste.
- Os arquivos `tests/test_*.py` funcionam como **especificacao**: leia antes de implementar.
- Testes marcados com `@pytest.mark.skip` sao **guias** das features do roadmap.
  Ao implementar, remova o `skip`.
- Rode um teste so: `pytest tests/test_db_connector.py -v`.

## 4. Estilo

- Docstrings em portugues explicando **o que** o modulo faz e **por que**.
- Nomes de funcoes/variaveis claros; evite abreviacoes.
- Nada de `print`; use mensagens na UI.
- Uma responsabilidade por arquivo (veja `docs/ARQUITETURA.md`).

## 5. Receitas

### Adicionar um sinonimo ao Motor Offline

1. Abra `chat_sql/nl/lexicon.py`.
2. Se for uma unidade ("anos" -> idade), adicione em `SEMANTIC_HINTS`.
3. Se for um valor de medida ("faturamento" -> valor_total), ajuste `MEASURE_KEYWORDS`.
4. Rode `pytest tests/test_offline_extended.py -v`.

### Adicionar um novo padrao de pergunta

1. Entenda o fluxo em `chat_sql/nl/engine.py` (`_detect_aggregation`, `_extract_*`).
2. Escreva o teste primeiro (em `tests/`).
3. Implemente o minimo para passar.
4. Atualize o `PRD.md` (secao "O que o Motor Offline entende", no README).

### Adicionar uma nova Fonte de Dados (ex.: banco real)

1. Leia `chat_sql/datasource.py` (a interface).
2. Implemente `schema()` e `execute()`.
3. Ligue na UI (`app.py`) como uma nova opcao na aba Dados.
4. Ative os testes-guia correspondentes.

## 6. Decisoes (ADRs)

Decisoes importantes viram um arquivo em `docs/adr/`, no formato `NNNN-titulo.md`, com
1-3 frases (contexto, decisao, por que). Numere seguindo o ultimo existente.
Exemplos: por que conexao read-only (0008), por que motor offline (0005).

## 7. Definicao de pronto

- [ ] `pytest` verde.
- [ ] Teste cobrindo o comportamento novo.
- [ ] Docstring/comentario onde a logica nao for obvia.
- [ ] `ROADMAP.md` atualizado (tarefa marcada).
- [ ] PR revisado por outra pessoa.
