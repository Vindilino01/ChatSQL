# Como conectar no banco de demonstração

[Início](../README.md) · [Documentação do banco](mer/README.md)

O banco fica no **Neon** (PostgreSQL na nuvem) e é **somente leitura**: ninguém
consegue alterar nem apagar dados. São 7 tabelas e ~5.300 registros da
biblioteca.

---

## 1. Peça a senha

A senha **não fica neste repositório** (nem deve). Peça no privado para quem
administra o banco.

- **Host:** `ep-royal-hall-b6uo2i82-pooler.c-2.sa-east-1.aws.neon.tech`
- **Banco:** `neondb`
- **Usuário:** `chatsql_ro`
- **SSL:** obrigatório (`sslmode=require`)

## 2. Monte a URL

Cole tudo numa linha só:

```
postgresql+psycopg://chatsql_ro:SUA_SENHA@ep-royal-hall-b6uo2i82-pooler.c-2.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

> O trecho `+psycopg` é obrigatório. Sem ele, o SQLAlchemy pode não encontrar o
> driver instalado.

## 3. Rode o app

```powershell
cd ChatSQL
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Abra `http://localhost:8501`.

> **Erro `venvlauncher.exe` ao criar o ambiente?** Algumas instalações do
> Python 3.14 vêm sem os launchers do `venv`. Nesse caso use:
>
> ```powershell
> python -m pip install virtualenv
> python -m virtualenv venv
> ```

## 4. Conecte

1. Aba **Dados**
2. Marque **Banco de dados (Postgres/SQLite)**
3. Cole a URL no campo **URL de conexão**
4. Deixe **Tabelas permitidas** vazio (assim vê as 7)
5. Clique **Conectar e usar**

Aguarde: na primeira conexão o Neon leva alguns segundos para "acordar".

## 5. Confira

Na barra da esquerda deve aparecer:

```
Fonte ativa
Banco: postgres (7 tabelas)
```

E abaixo a lista: `autor`, `editora`, `emprestimo`, `exemplar`, `livro`,
`livro_autor`, `usuario`.

## 6. Teste

Aba **Chat**, digite:

| Pergunta | Esperado |
|---|---|
| `quantos livros existem` | 456 |
| `quais editoras existem` | 40 |
| `quais os 5 livros mais antigos` | 1532, 1572, 1597... |
| `quantos emprestimos por mes` | tabela + gráfico |
| `quais livros com titulo Dom Casmurro` | 1 resultado |

---

## Problemas comuns

| Mensagem | Causa | Solução |
|---|---|---|
| `could not translate host name` | URL incompleta | confira o host inteiro |
| `password authentication failed` | senha errada | peça de novo; cuidado com espaços |
| `connection refused` / timeout | rede ou Neon dormindo | tente de novo; a primeira conexão demora |
| `ModuleNotFoundError: psycopg` | dependências não instaladas | `pip install -r requirements.txt` |
| `A conexão funcionou, mas nenhuma tabela foi encontrada` | filtro de tabelas digitado errado | deixe o campo vazio |
| `Somente SELECT é permitido` | você tentou alterar dados | é o comportamento esperado |

## Se não houver banco disponível

O app funciona **sem banco nenhum**:

1. Aba **Dados** → **Schema de exemplo**
2. Escolha `e-commerce`, `rh` ou `vendas`
3. **Carregar exemplo**

Dados sintéticos, mesmas funcionalidades, tudo offline.

---

[Início](../README.md) · [Documentação do banco](mer/README.md)
