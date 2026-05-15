# ChatFGV
Hackathon de pergunta aos dados via LLM.

## Objetivo
Responder perguntas sobre os verbetes do DHBB num chat privado da FGV no Teams.

## Project Overview

**ChatFGV** is a RAG-based hackathon project that implements a question-answering system over the DHBB (Dicionário Histórico-Biográfico Brasileiro – Brazilian Historical-Biographical Dictionary) dataset. The project is currently in the article publication phase for a scientific journal (H2D – Digital Humanities).

**Key goal**: Enable users to query historical biographical data via natural language through an LLM-powered chat interface.

## Architecture Overview

### RAG Pipeline

1. **Data Preparation**: DHBB verbetes (text files) are chunked and embedded
2. **Retrieval**: Query text is embedded; semantic search retrieves relevant verbetes
3. **Generation**: Retrieved context is passed to local LLM for answer generation
4. **Interface**: Streamlit UI or FastAPI endpoints expose the system

**Key components**:
- **Embedding**: `PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir` (Serafim, otimizado para portugues)
- **Vector Store**: FAISS (for semantic search)
- **LLM Runtime**: copilot (inside codespaces)

### Agent System (IBGE)

A two-stage agent system for SQL-based queries:
1. **Agent 1**: Receives user prompt + database schema → generates SQL query
2. **Agent 2**: Executes query, receives results + original prompt → generates final answer

This architecture decouples data complexity from LLM load, allowing large datasets via Postgres to be queried efficiently.
