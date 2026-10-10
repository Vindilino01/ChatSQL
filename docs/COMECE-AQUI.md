# Comece aqui (para quem nunca programou)

Este guia ensina, do zero, a **abrir o projeto, rodar o app e rodar os testes**.
Não precisa saber programar para seguir os passos.

Se você usa Windows, os comandos abaixo funcionam. Em outros sistemas, veja as observações.

[Início](../README.md) · [Índice](README.md) · [Mapa: onde fica o quê](ONDE-FICA-O-QUE.md)

---

## Como o projeto funciona (em uma imagem)

```
Você escreve:   "quantos clientes existem?"
        |
        v
  O robô entende a pergunta
        |
        v
  Ele escreve o SQL:   SELECT COUNT(*) FROM clientes;
        |
        v
  A Trava confere: é só leitura? as colunas existem?
        |
        v
  Você vê o SQL na tela e clica em Executar
        |
        v
  O resultado aparece na tabela (e no gráfico)
```

---

## O que você vai instalar

| Programa | Para que serve |
|---|---|
| **Python** | A linguagem em que o projeto foi escrito |
| **VS Code** | O editor onde você vai ver e mexer nos arquivos |
| **Git** | Guarda as versões e envia as mudanças para o GitHub |

---

## Passo 1 - Instalar o Python

1. Acesse https://www.python.org/downloads/
2. Baixe a versão mais recente e instale.
3. **Importante (Windows):** na primeira tela da instalação, marque a caixinha
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

Escolha **uma** das opções.

### Opção A - Pelo VS Code (mais fácil)

1. Abra o VS Code.
2. Aperte `Ctrl + Shift + P` e digite `Git: Clone`.
3. Cole o endereço: `https://github.com/Vindilino01/ChatSQL.git`
4. Escolha uma pasta no seu computador (ex.: Área de Trabalho).
5. Clique em **Open** quando ele perguntar se quer abrir.

### Opção B - Pelo site

1. Abra https://github.com/Vindilino01/ChatSQL
2. Clique no botão verde **Code** e depois em **Download ZIP**.
3. Descompacte o arquivo na Área de Trabalho.
4. No VS Code: menu **File > Open Folder** e escolha a pasta.

---

## Passo 5 - Abrir o terminal dentro do VS Code

No VS Code, aperte `Ctrl + '` (control com o acento ao lado do 1) ou use o menu
**Terminal > New Terminal**. Vai aparecer uma telinha na parte de baixo para digitar comandos.

---

## Passo 6 - Preparar o projeto (só na primeira vez)

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

Deve aparecer algo como `133 passed, 6 skipped`. Isso significa que está tudo certo.

---

## Como salvar e enviar uma mudança

Sempre que você mexer em algum arquivo e quiser mandar para o GitHub:

```powershell
git pull
git checkout -b meu-nome/minha-tarefa
git add .
git commit -m "Descreva em uma frase o que você fez"
git push -u origin meu-nome/minha-tarefa
```

Depois, abra o repositório no GitHub e clique no botão **Compare & pull request**.
Preencha o modelo que aparecer e peça para alguém revisar.

Dica: rode os testes **antes** de enviar:

```powershell
.\venv\Scripts\python -m pytest -q
```

---

## Dicionário rápido

| Palavra | O que quer dizer |
|---|---|
| Terminal | A telinha onde você digita comandos |
| Repositório | A pasta do projeto que fica no GitHub |
| Commit | Um "salvar" com uma mensagem explicando o que mudou |
| Branch | Uma cópia paralela para você trabalhar sem atrapalhar os outros |
| Pull Request (PR) | O pedido para juntar a sua mudança ao projeto principal |
| pytest | O programa que roda os testes do projeto |

---

## Deu problema?

- **"python não é reconhecido"**: reinstale o Python marcando "Add python.exe to PATH".
- **"streamlit não é reconhecido"**: use sempre `.\venv\Scripts\streamlit run app.py` (com o caminho da venv).
- **Não sabe por onde começar a trabalhar**: veja [ONDE-FICA-O-QUE.md](ONDE-FICA-O-QUE.md) e o guia da sua frente em [frentes/](frentes/).

---

[Início](../README.md) · [Índice](README.md) · [Mapa: onde fica o quê](ONDE-FICA-O-QUE.md)
