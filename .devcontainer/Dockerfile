FROM rocker/r-ver:4.4.2

# ============================================================
# ChatFGV - Imagem GitHub Codespaces com RAG + Copilot Code
# ============================================================
# Imagem otimizada para build rapido no Codespaces.
# O indice FAISS e construido no setup.sh (postCreateCommand).
# NAO ha Ollama ou LLM local - a geracao de respostas e
# feita pelo proprio GitHub Copilot Chat.
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
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

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
    polars

# Locale pt_BR
RUN sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=pt_BR.UTF-8

# Pacotes R
RUN R -e "install.packages(c('IRkernel', 'languageserver'), repos='https://cloud.r-project.org', Ncpus=2)" && \
    R -e "IRkernel::installspec(user = FALSE)"

# Criar usuario vscode (compativel com Codespaces)
RUN useradd -m -s /bin/bash vscode && \
    usermod -aG sudo vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# ============================================================
# COPIAR ARQUIVOS DO PROJETO
# ============================================================
# O indice FAISS e construido no setup.sh (postCreateCommand).
COPY DHBB/ /workspaces/ChatFGV/DHBB/
COPY RAG-streamlit-api/ /workspaces/ChatFGV/RAG-streamlit-api/
COPY dhbb-query.py /workspaces/ChatFGV/dhbb-query.py

# Criar diretorios e dar permissoes
RUN mkdir -p /workspaces/ChatFGV/faiss_index && \
    chown -R vscode:vscode /workspaces/ChatFGV

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
