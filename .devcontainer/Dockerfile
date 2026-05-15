FROM rocker/r-ver:4.4.2

# ============================================================
# ChatFGV - Imagem GitHub Codespaces com RAG + PostgreSQL + Copilot
# ============================================================
# Imagem otimizada para build rapido no Codespaces.
# O indice FAISS e construido no setup.sh (postCreateCommand).
# PostgreSQL é iniciado automaticamente no Codespaces.
# Consultas SQL podem ser executadas via CLI/API para testes.
# ============================================================

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgit2-dev \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    git-lfs \
    curl \
    vim \
    ripgrep \
    ffmpeg \
    sudo \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    dirmngr \
    procps \
    postgresql \
    postgresql-contrib \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

#    postgresql \


# Iniciar servico PostgreSQL no container (para uso local, se precisar)
# No Codespaces, o servico sera iniciado via 'services-start' conforme devcontainer.json
# RUN service postgresql start 2>/dev/null || true

# Criar link simbolico para python
RUN ln -sf /usr/bin/python3 /usr/local/bin/python

# Instalar GitHub Copilot CLI
RUN curl -fsSL https://gh.io/copilot-install | bash

# Instalar Python packages essenciais (RAG + ferramentas)
# PyTorch CPU em etapa separada para evitar conflitos
RUN pip3 install --no-cache-dir --break-system-packages \
    torch==2.5.1+cpu --index-url https://download.pytorch.org/whl/cpu

RUN pip3 install --no-cache-dir --break-system-packages \
    jupyterlab \
    notebook \
    ipykernel \
    pandas \
    numpy \
    scipy \
    scikit-learn \
    matplotlib \
    seaborn \
    plotly \
    streamlit \
    faiss-cpu \
    langchain \
    langchain-core \
    langchain-community \
    langchain-text-splitters \
    sentence-transformers \
    pyyaml \
    httpx \
    rich \
    pyarrow \
    polars \
    psycopg2-binary \
    sqlalchemy

# Locale pt_BR
RUN sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=pt_BR.UTF-8

# Criar usuario vscode (compativel com Codespaces)
RUN useradd -m -s /bin/bash vscode && \
    usermod -aG sudo vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# ============================================================
# COPIAR ARQUIVOS DO PROJETO
# ============================================================
# O indice FAISS e construido no setup.sh (postCreateCommand).
# Caminhos ajustados ao contexto do repositório
COPY DHBB/ /workspaces/ChatFGV/DHBB/
COPY dhbb-query.py /workspaces/ChatFGV/dhbb-query.py

# dar permissoes
RUN chown -R vscode:vscode /workspaces/ChatFGV

# Configurar diretorio de trabalho
WORKDIR /workspaces

# Mudar para usuario vscode
USER vscode

# Variaveis de ambiente para o usuario
ENV PATH="/home/vscode/.local/bin:$PATH" \
    LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt:en_US:en \
    LC_ALL=pt_BR.UTF-8 \
    CHATFGV_INDEX="/workspaces/ChatFGV/faiss_index" \
    CHATFGV_DHBB="/workspaces/ChatFGV/DHBB/text"

# Switch back to root to install scripts to /usr/local/bin
USER root

# Adicionar helpers CLI para consultas SQL (testar conexao, rodar queries)
# Usam sudo -u postgres para autenticacao integrada via socket Unix
# (pg_hba.conf configurado com trust para conexoes locais)
# t: /usr/local/bin/dhbb-sql-test
# t: /usr/local/bin/dhbb-sql-query
RUN printf '#!/bin/bash\nset -e\nsudo -u postgres psql -c "$@"\n' > /usr/local/bin/dhbb-sql-query && \
    chmod +x /usr/local/bin/dhbb-sql-query && \
    printf '#!/bin/bash\nset -e\nsudo -u postgres psql -c "SELECT 1 as ok;"\n' > /usr/local/bin/dhbb-sql-test && \
    chmod +x /usr/local/bin/dhbb-sql-test

# Switch back to vscode user
USER vscode