# Bem-vindo ao ChatFGV

Este ambiente permite que voce faca perguntas a **bases de dados publicas brasileiras** usando inteligencia artificial, sem necessidade de instalacao ou configuracao tecnica.

## Bases de Dados Disponiveis

### Dados Nao Estruturados (RAG)
- **DHBB** (Dicionario Historico-Biografico Brasileiro) - 7.863 verbetes biograficos da FGV/CPDOC

### Dados Estruturados (PostgreSQL)
- **Acidentes de Transito** - ~73.156 registros de acidentes rodoviarios (PRF, 2024)
- **Censo Demografico** - ~468.099 setores censitarios com dados demograficos (IBGE, 2022)
- **Contagem de Trafego** - ~6.769 trechos rodoviarios com volume de trafego (DNIT, 2020)

## Primeiro Acesso

Ao abrir o Codespaces pela primeira vez, o ambiente leva **~10 minutos** para ficar pronto.
O tempo de vetorizacao com o modelo Serafim (otimizado para portugues) foi economizado, pois o indice ja esta salvo no repositorio.
O script de instalacao faz o seguinte automaticamente:

1. Instala pacotes necessarios para operacionalizar o RAG (leitura de bases de dados nao estruturadas)
2. Instala pacotes necessarios para operar com o postgres (leitura de bases de dados estruturadas)

Aguarde ate ver a mensagem **"ChatFGV - Ambiente Pronto!"** no terminal.

## Como Usar

### Metodo 1: GitHub Copilot Code (Recomendado)

1. Abra o **Copilot Code** (icone na barra lateral ou `Ctrl+I`)
2. Faca sua pergunta diretamente no chat. Exemplos:

**Perguntas sobre o DHBB:**
- *"Quem foi Getulio Vargas?"*
- *"O que foi a Revolucao de 1930?"*
- *"Quais cargos Juscelino Kubitschek ocupou?"*

**Perguntas sobre acidentes de transito:**
- *"Quantos acidentes fatais ocorreram em 2024?"*
- *"Qual a causa mais comum de acidentes no Brasil?"*
- *"Quais estados tiveram mais mortos em acidentes?"*

**Perguntas sobre o Censo:**
- *"Qual a populacao do Brasil according ao Censo 2022?"*
- *"Quantos setores sao urbanos vs rurais?"*
- *"Qual a taxa de alfabetizacao do Brasil?"*

**Perguntas sobre trafego:**
- *"Quais trechos da BR-101 tem maior volume de trafego?"*
- *"Qual o percentual de veiculos pesados nas rodovias federais?"*

3. O Copilot ira buscar automaticamente o contexto na base de dados e **gerar a resposta usando seu proprio modelo**, com citacao de fontes.

### Metodo 2: Terminal

**Para perguntas ao DHBB (busca semantica):**
```bash
python3 dhbb-query.py "Quem foi Getulio Vargas?"
```

Para saida em JSON (usado pelo Copilot):
```bash
python3 dhbb-query.py --json "Quem foi Getulio Vargas?"
```

**Para consultas SQL nas bases estruturadas:**
```bash
# Listar tabelas disponiveis
psql -U postgres -d public -c "\dt *.*"

# Consultar acidentes de transito
psql -U postgres -d public -c "SELECT COUNT(*) FROM datatran.acidentes_transito;"

# Consultar dados do Censo
psql -U postgres -d public -c "SELECT NM_UF, SUM(v0001) AS populacao FROM censo.br_setores_cd2022 GROUP BY NM_UF ORDER BY populacao DESC LIMIT 5;"

# Consultar contagem de trafego
psql -U postgres -d public -c "SELECT sg_uf, COUNT(*) FROM dnit.contagem_de_trafego_cgplan_dez20 GROUP BY sg_uf;"
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

## Sobre as Bases de Dados

### DHBB
O **Dicionario Historico-Biografico Brasileiro** e uma obra de referencia produzida pelo Centro de Pesquisa e Documentacao de Historia Contemporanea do Brasil (CPDOC) da Fundacao Getulio Vargas. Contem verbetes biograficos de personalidades que marcaram a historia brasileira.

### Acidentes de Transito
Dados de acidentes em rodovias federais brasileiras, com informacoes sobre localizacao, causa, tipo de acidente e vitimas. Fonte: Policia Rodoviaria Federal (PRF).

### Censo Demografico
Dados do Censo Demografico 2022 do IBGE, agregados por setores censitarios de todo o Brasil. Inclui informacoes geograficas, demograficas, de alfabetizacao e mortalidade.

### Contagem de Trafego
Dados de Volume Medio Diario Anual (VMDa) estimado por categoria de veiculo, por trecho da rede rodoviaria federal brasileira. Fonte: DNIT/CGPlan.

## Tecnologias Utilizadas

- **RAG (Retrieval-Augmented Generation)**: Busca semantica nos verbetes via FAISS + geracao de respostas pelo GitHub Copilot
- **FAISS**: Indice vetorial para busca semantica rapida nos 7.863 verbetes
- **Embeddings locais**: `PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir` (Serafim, otimizado para portugues, CPU, sem API keys)
- **Geracao pelo Copilot**: O proprio GitHub Copilot gera as respostas com base no contexto recuperado
- **PostgreSQL**: Banco de dados relacional para consultas SQL nas bases estruturadas

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
Alerta: no ambiente do codespaces a reconstrucao do indice FAISS nao vai funcionar porque nao tem GPU.

**Verificar status completo:**
```bash
chatfgv-status
```

**Copilot nao esta respondendo com contexto do DHBB:**
Verifique se as extensoes `GitHub.copilot` e `GitHub.copilot-chat` estao instaladas.

**PostgreSQL nao conecta:**
```bash
sudo service postgresql start
```

---

**Projeto ChatFGV** - Artigo submetido a revista Humanidades Digitais (H2D), Universidade do Minho.
