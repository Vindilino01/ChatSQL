# Frente E - Entrega e Apresentação

**Responsáveis:** (preencher)

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)

---

## Em uma frase

Colocar o projeto no ar para qualquer pessoa rodar (**serviço**) e montar a
apresentação final.

## Onde fica no projeto

| Arquivo / pasta | O que é |
|---|---|
| `Dockerfile` | **A criar**: receita para rodar o app em qualquer computador. |
| `docker-compose.yml` | **A criar**: sobe o app (e um Postgres de demonstração, se quiser). |
| `.github/workflows/tests.yml` | **A criar**: roda os testes a cada envio (CI). |
| `.github/ISSUE_TEMPLATE/tarefa.md` | Modelo de tarefa (Issue). |
| `.github/pull_request_template.md` | Modelo de envio (Pull Request). |
| `PRD.md` | Documento do projeto; aqui entram os **resultados** (acurácia, prints). |
| `docs/imagens/` | Onde colocar os prints das telas. |
| `README.md` | Porta de entrada; precisa estar claro e com os links certos. |

## Primeira tarefa (passo a passo): Docker

1. Crie o arquivo `Dockerfile` na raiz. Um modelo simples:
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   EXPOSE 8501
   CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```
2. Crie o `docker-compose.yml` (opcional, já com Postgres):
   ```yaml
   services:
     app:
       build: .
       ports:
         - "8501:8501"
   ```
3. Teste:
   ```powershell
   docker compose up --build
   ```
4. Abra `http://localhost:8501`.

## Segunda tarefa: CI (testes automáticos)

1. Crie `.github/workflows/tests.yml`:
   ```yaml
   name: tests
   on: [push, pull_request]
   jobs:
     pytest:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: "3.12"
         - run: pip install -r requirements-dev.txt
         - run: pytest -q
   ```
2. Cada envio passa a rodar os testes sozinho. O resultado aparece na aba **Actions** do GitHub.

## Terceira tarefa: apresentação

1. Preencha o `PRD.md`:
   - seção **Resultados**: acurácia do motor offline (Frente B);
   - prints das telas (veja `docs/imagens/README.md`).
2. Monte os slides: problema, solução, como funciona, segurança, resultados, demo.
3. Faça um **vídeo de backup** da demo (caso o computador falhe no dia).
4. Ensaiem: a demo deve caber em 10 minutos.

## Como testar

```powershell
docker compose up --build
.\venv\Scripts\python -m pytest -q
```

## Pronto quando

- [ ] `docker compose up` funciona a partir de um clone limpo.
- [ ] Os testes rodam sozinhos a cada envio (badge verde no README).
- [ ] `PRD.md` com resultados e prints.
- [ ] Slides prontos e demo ensaiada (com vídeo de backup).

## Mini-glossário

| Palavra | O que quer dizer |
|---|---|
| Docker | Uma "caixa" que roda o projeto em qualquer computador |
| CI | Testes que rodam sozinhos a cada envio |
| Deploy | Colocar o projeto no ar para as pessoas usarem |
| Badge | Selo verde/vermelho no README mostrando se está tudo ok |

---

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md) · [Roadmap](../../ROADMAP.md)
