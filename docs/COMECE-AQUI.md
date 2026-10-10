# Comece aqui (para quem nunca programou)

Este guia ensina, do zero, a **abrir o projeto, rodar o app e rodar os testes**.
Nao precisa saber programar para seguir os passos.

Se voce usa Windows, os comandos abaixo funcionam. Em outros sistemas, veja as observacoes.

---

## O que voce vai instalar

| Programa | Para que serve |
|---|---|
| **Python** | A linguagem em que o projeto foi escrito |
| **VS Code** | O editor onde voce vai ver e mexer nos arquivos |
| **Git** | Guarda as versoes e envia as mudancas para o GitHub |

---

## Passo 1 - Instalar o Python

1. Acesse https://www.python.org/downloads/
2. Baixe a versao mais recente e instale.
3. **Importante (Windows):** na primeira tela da instalacao, marque a caixinha
   **"Add python.exe to PATH"** antes de clicar em Install.

Para conferir, abra o **Prompt de Comando** (tecle `Windows`, digite `cmd` e Enter) e rode:

```powershell
python --version
```

Deve aparecer algo como `Python 3.14.x`.

---

## Passo 2 - Instalar o VS Code

1. Acesse https://code.visualstudio.com/ e instale.
2. Abra o VS Code.

---

## Passo 3 - Instalar o Git

1. Acesse https://git-scm.com/downloads e instale (pode clicar "Next" em tudo).

Para conferir:

```powershell
git --version
```

---

## Passo 4 - Baixar o projeto

Escolha **uma** das opcoes.

### Opcao A - Pelo VS Code (mais facil)

1. Abra o VS Code.
2. Aperte `Ctrl + Shift + P` e digite `Git: Clone`.
3. Cole o endereco: `https://github.com/Vindilino01/ChatSQL.git`
4. Escolha uma pasta no seu computador (ex.: Area de Trabalho).
5. Clique em **Open** quando ele perguntar se quer abrir.

### Opcao B - Pelo site

1. Abra https://github.com/Vindilino01/ChatSQL
2. Clique no botao verde **Code** e depois em **Download ZIP**.
3. Descompacte o arquivo na Area de Trabalho.
4. No VS Code: menu **File > Open Folder** e escolha a pasta.

---

## Passo 5 - Abrir o terminal dentro do VS Code

No VS Code, aperte `Ctrl + '` (control com o acento ao lado do 1) ou use o menu
**Terminal > New Terminal**. Vai aparecer uma telinha na parte de baixo para digitar comandos.

---

## Passo 6 - Preparar o projeto (so na primeira vez)

Copie e cole os comandos abaixo no terminal, um por vez, apertando Enter:

```powershell
python -m venv venv
```

Isso cria a "caixa de ferramentas" do projeto (pasta `venv`). Depois:

```powershell
.\venv\Scripts\python -m pip install -r requirements.txt
```

Isso instala tudo o que o projeto precisa. Pode demorar um pouco.

---

## Passo 7 - Rodar o app

```powershell
.\venv\Scripts\streamlit run app.py
```

O navegador abre sozinho em `http://localhost:8501`.
No app: aba **Dados** -> escolha uma fonte -> aba **Chat** -> pergunte.
Para parar, volte ao terminal e aperte `Ctrl + C`.

---

## Passo 8 - Rodar os testes

```powershell
.\venv\Scripts\python -m pytest -q
```

Deve aparecer algo como `133 passed, 6 skipped`. Isso significa que esta tudo certo.

---

## Como salvar e enviar uma mudanca

Sempre que voce mexer em algum arquivo e quiser mandar para o GitHub:

```powershell
git pull
git checkout -b meu-nome/minha-tarefa
git add .
git commit -m "Descreva em uma frase o que voce fez"
git push -u origin meu-nome/minha-tarefa
```

Depois, abra o repositorio no GitHub e clique no botao **Compare & pull request**.
Preencha o modelo que aparecer e peca para alguem revisar.

Dica: rode os testes **antes** de enviar:

```powershell
.\venv\Scripts\python -m pytest -q
```

---

## Dicionario rapido

| Palavra | O que quer dizer |
|---|---|
| Terminal | A telinha onde voce digita comandos |
| Repositorio | A pasta do projeto que fica no GitHub |
| Commit | Um "salvar" com uma mensagem explicando o que mudou |
| Branch | Uma copia paralela para voce trabalhar sem atrapalhar os outros |
| Pull Request (PR) | O pedido para juntar a sua mudanca ao projeto principal |
| pytest | O programa que roda os testes do projeto |

---

## Deu problema?

- **"python nao e reconhecido"**: reinstale o Python marcando "Add python.exe to PATH".
- **"streamlit nao e reconhecido"**: use sempre `.\venv\Scripts\streamlit run app.py` (com o caminho da venv).
- **Nao sabe por onde comecar a trabalhar**: veja [ONDE-FICA-O-QUE.md](ONDE-FICA-O-QUE.md) e o guia da sua frente em [frentes/](frentes/).
