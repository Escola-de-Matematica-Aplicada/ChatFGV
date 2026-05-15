# Bem-vindo ao ChatFGV

Este ambiente permite que voce faca perguntas ao **Dicionario Historico-Biografico Brasileiro (DHBB)** da FGV/CPDOC usando inteligencia artificial, sem necessidade de instalacao ou configuracao tecnica.

## Primeiro Acesso

Ao abrir o Codespaces pela primeira vez, o ambiente leva **~10 minutos** para ficar pronto.
O tempo de vetorização com o modelo Serafim (otimizado para portugues) foi economizado, pois o índice já está salvo no repositório.
O script de instalacao faz o seguinte automaticamente:

1. Instala pacotes necessários para operacionalizar o RAG (leitura de bases de dados não estruturadas)
2. Instala pacotes necessários para operar com o postgres (leitura de bases de dados estruturadas)

Aguarde ate ver a mensagem **"ChatFGV - Ambiente Pronto!"** no terminal.

## Como Usar

### Metodo 1: GitHub Copilot Code (Recomendado)

1. Abra o **Copilot Code** (icone na barra lateral ou `Ctrl+I`)
2. Faca sua pergunta diretamente no chat. Exemplos:
   - *"Quem foi Getulio Vargas?"*
   - *"O que foi a Revolucao de 1930?"*
   - *"Quais cargos Juscelino Kubitschek ocupou?"*
3. O Copilot ira buscar automaticamente o contexto na base de 7.863 verbetes do DHBB e **gerar a resposta usando seu proprio modelo**, com citacao de fontes.

### Metodo 2: Terminal (apenas busca)

Abra um terminal e digite:

```bash
  python3 dhbb-query.py "Quem foi Getulio Vargas?"
```

Isso retorna os documentos relevantes do DHBB. Para saida em JSON (usado pelo Copilot):

```bash
  python3 dhbb-query.py --json "Quem foi Getulio Vargas?"
```

Isso e util para verificar o que o sistema esta recuperando do DHBB. Para limitar o numero de resultados:
```bash
  python3 dhbb-query.py --top-k 3 "O que foi a Revolucao de 1930?"
```

Isso é útil para entender o que o sistema esta buscando e como as respostas sao construidas.
```bash
  python3 dhbb-query.py --check
```

## Status do Sistema

Para verificar se tudo esta funcionando:

```bash
dhbb --check
```

Ou o alias completo:

```bash
chatfgv-status
```

## Sobre o DHBB

O **Dicionario Historico-Biografico Brasileiro** e uma obra de referencia produzida pelo Centro de Pesquisa e Documentacao de Historia Contemporanea do Brasil (CPDOC) da Fundacao Getulio Vargas. Contem verbetes biograficos de personalidades que marcaram a historia brasileira.

Este ambiente utiliza:
- **RAG (Retrieval-Augmented Generation)**: Busca semantica nos verbetes via FAISS + geracao de respostas pelo GitHub Copilot
- **FAISS**: Indice vetorial para busca semantica rapida nos 7.863 verbetes
- **Embeddings locais**: `PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir` (Serafim, otimizado para portugues, CPU, sem API keys)
- **Geracao pelo Copilot**: O proprio GitHub Copilot gera as respostas com base no contexto recuperado

## Perguntas de Exemplo

- *"Quem foi Tancredo Neves?"*
- *"O que foi o Estado Novo?"*
- *"Quem foram os presidentes do Brasil na Republica Velha?"*
- *"Qual foi o papel de Carlos Lacerda na politica brasileira?"*
- *"O que aconteceu na Revolucao Constitucionalista de 1932?"*

## Notas

- Este ambiente roda inteiramente no GitHub Codespaces - seus dados e perguntas sao processados de forma privada
- A geracao de respostas e feita pelo GitHub Copilot (modelo na nuvem), sem necessidade de LLM local
- O indice FAISS e construido automaticamente pelo script de setup (postCreateCommand)
- O setup e mais rapido que versoes anteriores pois nao baixa modelos LLM locais

## Solucao de Problemas

**Indice FAISS nao encontrado:**
```bash
cd /workspaces/ChatFGV && python3 dhbb-query.py --build-index
```
Alerta: no ambiente do codespaces a reconstrução do índice FAISS não vai funcionar porque não tem GPU.

**Verificar status completo:**
```bash
chatfgv-status
```

**Copilot nao esta respondendo com contexto do DHBB:**
Verifique se as extensoes `GitHub.copilot` e `GitHub.copilot-chat` estao instaladas.

---

**Projeto ChatFGV** - Artigo submetido a revista Humanidades Digitais (H2D), Universidade do Minho.
