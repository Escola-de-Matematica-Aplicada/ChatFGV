# Bem-vindo ao Pergunte aos Dados

Este ambiente permite que voce faca perguntas ao **Dicionario Historico-Biografico Brasileiro (DHBB)** da FGV/CPDOC e a **bases de dados publicas estruturadas** usando inteligencia artificial, sem necessidade de instalacao ou configuracao tecnica.

## Bases Disponiveis

### Nao-estruturadas (RAG com embeddings)
- **DHBB** — Dicionario Historico-Biografico Brasileiro (7.863 verbetes)

### Estruturadas (SQL via PostgreSQL)
- **Acidentes de Transito** — Dados do DNIT/DataTran (2024, ~73 mil registros)
- **Censo 2022 (Setores)** — Estrutura geografica dos setores censitarios do IBGE (~468 mil registros)
- **Censo 2022 (Educacao Basica)** — Indicadores de educacao por setor (~458 mil registros)
- **Censo 2022 (Alfabetizacao)** — Dados de alfabetizacao por setor (~458 mil registros)
- **Censo 2022 (Obitos)** — Dados de obitos por setor (~458 mil registros)
- **Contagem de Trafego** — Volume de trafego em rodovias federais (DNIT/CGPLAN, Dez/2020, ~6.700 registros)

## Primeiro Acesso

Ao abrir o Codespaces pela primeira vez, o ambiente leva **~10 minutos** para ficar pronto.
O tempo de vetorização com o modelo Serafim (otimizado para portugues) foi economizado, pois o índice já está salvo no repositório.
O script de instalacao faz o seguinte automaticamente:

1. Instala pacotes necessários para operacionalizar o RAG (leitura de bases de dados não estruturadas)
2. Instala pacotes necessários para operar com o postgres (leitura de bases de dados estruturadas)

Aguarde ate ver a mensagem **"Pergunte aos Dados - Ambiente Pronto!"** no terminal.

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
  python3 pergunta-aos-dados/dhbb-query.py "Quem foi Getulio Vargas?"
```

Isso retorna os documentos relevantes do DHBB. Para saida em JSON (usado pelo Copilot):

```bash
  python3 pergunta-aos-dados/dhbb-query.py --json "Quem foi Getulio Vargas?"
```

Isso e util para verificar o que o sistema esta recuperando do DHBB. Para limitar o numero de resultados:
```bash
  python3 pergunta-aos-dados/dhbb-query.py --top-k 3 "O que foi a Revolucao de 1930?"
```

Isso é útil para entender o que o sistema esta buscando e como as respostas sao construidas.
```bash
  python3 pergunta-aos-dados/dhbb-query.py --check
```

### Metodo 3: Consultar Dados Estruturados (SQL)

Para perguntas sobre dados estruturados (acidentes, censo, trafego):

```bash
  python3 pergunta-aos-dados/structured-query.py "Quantos acidentes de transito houve em SP em 2024?"
  python3 pergunta-aos-dados/structured-query.py --json "Qual UF tem mais mortes no transito?"
  python3 pergunta-aos-dados/structured-query.py --list-tables
  python3 pergunta-aos-dados/structured-query.py --schema
  python3 pergunta-aos-dados/structured-query.py --check
  python3 pergunta-aos-dados/structured-query.py --build-index
```

O sistema combina busca semantica no dicionario de dados (FAISS) com consultas SQL (PostgreSQL).
A resposta final e gerada pelo GitHub Copilot.

### Metodo 4: Copilot Code para Dados Estruturados

No Copilot Code, voce tambem pode perguntar sobre dados estruturados:
- *"Quantos acidentes de transito houve em SP em 2024?"*
- *"Qual a regiao com mais mortes no transito?"*
- *"Quantas pessoas vivem em setores urbanos do Rio de Janeiro?"*
- *"Qual o volume medio diario de veiculos na BR-101?"*

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
cd /workspaces/pergunta-aos-dados/ && python3 dhbb-query.py --build-index
```
Alerta: no ambiente do codespaces a reconstrução do índice FAISS não vai funcionar porque não tem GPU.

**Verificar status completo:**
```bash
chatfgv-status
```

**Copilot nao esta respondendo com contexto do DHBB:**
Verifique se as extensoes `GitHub.copilot` e `GitHub.copilot-chat` estao instaladas.

---

**Projeto Pergunte aos Dados** - Artigo submetido a revista Humanidades Digitais (H2D), Universidade do Minho.
