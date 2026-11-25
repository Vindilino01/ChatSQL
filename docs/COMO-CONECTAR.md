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
3. Escolha como informar a conexão:
   - **Campos separados** (recomendado): preencha host, banco, usuário e senha;
   - **URL completa**: cole a linha do passo 2, se preferir.

   > A primeira vez pede tudo. Nas seguintes, **host, banco e usuário já vêm
   > preenchidos** — só a senha é pedida de novo. Ela nunca é gravada em disco.
4. Clique **Conectar e usar**

Aguarde: na primeira conexão o Neon leva alguns segundos para "acordar".

### Filtro de tabelas

Depois de conectar uma vez, aparece um **seletor com uma caixa por tabela**.
Desmarque o que não deve ser consultado (por exemplo, uma tabela de auditoria) e
conecte de novo. Deixar todas marcadas equivale a liberar o banco inteiro.

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
| `A conexão funcionou, mas nenhuma tabela foi encontrada` | filtro de tabelas errado | marque ao menos uma tabela no seletor |
| `Somente SELECT é permitido` | você tentou alterar dados | é o comportamento esperado |
| `A planilha não está pública` | link do Google sem permissão | Compartilhar → Qualquer pessoa com o link → Leitor |
| `O arquivo não contém CREATE TABLE` | o `.sql` só tem `INSERT` | envie o dump completo, com a estrutura |

## Se não houver banco disponível

O app funciona **sem banco nenhum**. Há cinco caminhos na aba **Dados**:

| Fonte | Quando usar |
|---|---|
| **Planilhas (CSV/Excel)** | Você já tem os dados em arquivo |
| **Google Sheets (link público)** | A planilha está no Google e é pública |
| **Banco de dados** | Existe um Postgres ou SQLite acessível |
| **Script SQL** | Você tem um `CREATE TABLE` / `INSERT` para colar |
| **Arquivo .sql (dump)** | Você tem o dump em arquivo, de um sistema antigo |
| **Schema de exemplo** | Não tem dado nenhum; quer só ver funcionando |

### Google Sheets

1. No Google Sheets: **Compartilhar → Qualquer pessoa com o link → Leitor**
2. Aba **Dados** → **Google Sheets (link público)**
3. Cole o link da planilha (o mesmo que você abriria no navegador)
4. **Carregar planilha do Google**

Baixa a primeira aba, ou a aba indicada no `gid` do link. Se a planilha não for
pública, o app avisa em vez de mostrar tela de login.

### Dump `.sql`

1. Aba **Dados** → **Arquivo .sql (dump)**
2. Envie o arquivo
3. **Carregar dump**

Aceita dois casos: dump **com dados** (`CREATE TABLE` + `INSERT INTO` — usa os
seus registros) ou só **estrutura** (gera dados de exemplo para você testar). Se
o arquivo não tiver `CREATE TABLE`, o app recusa com explicação.

**Dump do MySQL é aceito.** O app detecta as marcas do MySQL (`ENGINE=InnoDB`,
`AUTO_INCREMENT`, crases) e converte para o formato de execução antes de rodar —
`int(11)` vira `INTEGER`, índices `KEY nome (col)` são descartados, e os dados dos
`INSERT` são preservados. A descrição na tela mostra "convertido do MySQL". Vale
para dumps comuns; rotinas, triggers e `DELIMITER` não são convertidos.

> Limite: o arquivo é carregado em memória. Um dump de vários GB não é suportado.

### Schema de exemplo

1. Aba **Dados** → **Schema de exemplo**
2. Escolha `e-commerce`, `rh` ou `vendas`
3. **Carregar exemplo**

Dados sintéticos, mesmas funcionalidades, tudo offline.

---

[Início](../README.md) · [Documentação do banco](mer/README.md)
