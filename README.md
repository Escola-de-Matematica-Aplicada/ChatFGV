# ChatFGV
Hackathon de pergunta aos dados via LLM.

## Objetivo
Responder perguntas sobre bases de dados públicas brasileiras num chat privado da FGV no Teams.

## Project Overview

**ChatFGV** is a RAG-based hackathon project that implements a question-answering system over multiple Brazilian public databases. The project combines **unstructured data** (DHBB biographical dictionary) with **structured data** (traffic accidents, census, traffic count) to enable comprehensive data analysis.

**Key goal**: Enable users to query historical, demographic, and infrastructure data via natural language through an LLM-powered chat interface.

## Databases

### Unstructured Data (RAG Pipeline)
- **DHBB** (Dicionário Histórico-Biográfico Brasileiro) - 7,863 biographical entries from FGV/CPDOC

### Structured Data (PostgreSQL)
- **Acidentes de Trânsito** (Traffic Accidents) - ~73,156 records from PRF (2024)
- **Censo Demográfico** (Census) - ~468,099 census sectors with demographic data (2022)
- **Contagem de Tráfego** (Traffic Count) - ~6,769 road sections with volume data (DNIT/2020)

## Architecture Overview

### RAG Pipeline (DHBB)
1. **Data Preparation**: DHBB verbetes (text files) are chunked and embedded
2. **Retrieval**: Query text is embedded; semantic search retrieves relevant verbetes
3. **Generation**: Retrieved context is passed to LLM for answer generation
4. **Interface**: Streamlit UI or FastAPI endpoints expose the system

**Key components**:
- **Embedding**: `PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir` (Serafim, otimizado para portugues)
- **Vector Store**: FAISS (for semantic search)
- **LLM Runtime**: copilot (inside codespaces)

### Agent System (Structured Data)
A two-stage agent system for SQL-based queries:
1. **Agent 1**: Receives user prompt + database schema → generates SQL query
2. **Agent 2**: Executes query, receives results + original prompt → generates final answer

This architecture decouples data complexity from LLM load, allowing large datasets via Postgres to be queried efficiently.

## Database Schemas

### datatran (Traffic Accidents)
- `datatran.acidentes_transito` - Traffic accident records with location, time, cause, and victim data

### censo (Census)
- `censo.agregados_por_setores_alfabetizacao_br` - Literacy data by census sector (362 variables)
- `censo.agregados_por_setores_obitos_br` - Mortality data by census sector (93 variables)
- `censo.agregados_por_setores_basico_br` - Basic demographic data by census sector
- `censo.br_setores_cd2022` - Geographic and basic data by census sector

### dnit (Traffic Count)
- `dnit.contagem_de_trafego_cgplan_dez20` - Road traffic volume by section and vehicle category
