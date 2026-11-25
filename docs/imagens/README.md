# Imagens (prints das telas)

Coloque aqui as fotos das telas do projeto. Elas vão para o relatório e os
slides.

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md)

---

## Arquivos esperados

| Arquivo | O que deve mostrar |
|---|---|
| `tela-chat.png` | A pergunta digitada, o SQL gerado e o **número em destaque** |
| `tela-dados.png` | A aba Dados com a prévia das tabelas carregadas |
| `tela-configuracoes.png` | A tela de configurações com o provedor |
| `diagrama-er.png` | O diagrama do banco (gerado no draw.io) |
| `tela-grafico.png` | Um resultado com gráfico (ex.: "quantos empréstimos por mês") |

## Como tirar um print (Windows)

1. Aperte `Windows + Shift + S`
2. Selecione a área — prefira capturar **só a área do app**, sem o navegador
3. Cole (Ctrl + V) num programa de imagem ou salve direto
4. Renomeie com o nome exato da tabela acima

**Antes de capturar:**
- Deixe o app com zoom 100% (`Ctrl + 0` no navegador)
- Se a tela for grande, use uma janela de **1366×768** — é o tamanho do projetor
  da sala, e o que vocês virem é o que a banca vai ver
- Feche abas e notificações que apareçam na captura

## Como usar as imagens

### No relatório (`RELATORIO.md`, na raiz)

```markdown
![Diagrama entidade-relacionamento](docs/imagens/diagrama-er.png)
```

### Dentro da pasta `docs/`

```markdown
![Chat](imagens/tela-chat.png)
```

## O diagrama do banco

Siga [`docs/mer/README.md`](../mer/README.md). O caminho mais confiável:

1. Abra <https://app.diagrams.net>
2. **File → Open From → Device…** → escolha `docs/mer/biblioteca.drawio`
3. **File → Export as → PNG**, zoom 200%
4. Salve aqui como `diagrama-er.png`

---

[Início](../../README.md) · [Índice](../README.md) · [Mapa: onde fica o quê](../ONDE-FICA-O-QUE.md)
