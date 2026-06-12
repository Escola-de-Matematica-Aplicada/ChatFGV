FROM python:3.12-slim

# Instalar dependências do sistema
ENV DEBIAN_FRONTEND=noninteractive
# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgit2-dev \
    git \
    git-lfs \
    curl \
    vim \
    ripgrep \
    ffmpeg \
    sudo \
    gnupg2 \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    texlive-latex-extra \
    texlive-luatex \
    texlive-science \
    texlive-bibtex-extra \
    texlive-latex-base \
    texlive-fonts-extra \
    texlive-lang-portuguese \
    texlive-latex-recommended \
    pandoc \
    apt-transport-https \
    ca-certificates \
    dirmngr \
    locales \
    nodejs \
    npm \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# Generate and set pt_BR.UTF-8 locale
RUN sed -i 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=pt_BR.UTF-8

# Install uv package manager via pip (more reliable in Docker)
RUN pip install --no-cache-dir uv

# Set PATH for uv
ENV PATH="/root/.local/bin:${PATH}"

# Clone and install docker-mcp
RUN cd /opt && \
    git clone https://github.com/QuantGeekDev/docker-mcp.git && \
    cd docker-mcp && \
    uv sync

# Clone and install MarkItDown
RUN git clone https://github.com/microsoft/markitdown.git /opt/markitdown && \
    cd /opt/markitdown && \
    pip install --break-system-packages -e 'packages/markitdown[all]'

# Install CLI agents
# HERMES Agent
RUN mkdir -p /root/.hermes && \
    git clone https://github.com/NousResearch/hermes-agent.git /root/.hermes/hermes-agent && \
    curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Install HERMES Agent MCP extras
RUN cd /root/.hermes/hermes-agent && \
    uv pip install --system -e ".[mcp]"

# Kilo Code
RUN curl -fsSL https://kilo.ai/cli/install | bash

# Kimi
RUN curl -L code.kimi.com/install.sh | bash

# Claude
RUN curl -fsSL https://claude.ai/install.sh | bash

# Vibe (Mistral)
RUN curl -LsSf https://mistral.ai/vibe/install.sh | bash

# Grok CLI
RUN npm install -g @vibe-kit/grok-cli

# Install Gemini CLI
RUN npm install -g @google/gemini-cli

# Install copilot cli
RUN npm install -g @github/copilot

# Install Antigratity cli
RUN curl -fsSL https://antigravity.google/cli/install.sh | bash

# Install MiMo Code
RUN curl -fsSL https://mimo.xiaomi.com/install | bash \

# Install Python packages
RUN pip install --no-cache-dir --break-system-packages \
    polars>=1.0.0 \
    radian \
    stemgraphic \
    matplotlib \
    seaborn \
    pandas \
    numpy \
    scipy \
    scikit-learn \
    plotly \
    pyarrow \
    clickhouse-driver \
    clickhouse-connect \
    poppler-utils \
    PyMuPDF  # Adiciona o PyMuPDF (que fornece o módulo fitz)

# Set environment variables
ENV LANG=pt_BR.UTF-8 \
    LANGUAGE=pt_BR:pt:en_US:en \
    LC_ALL=pt_BR.UTF-8 \
    PATH="/root/.local/bin:$PATH"

# Configurar diretório de trabalho
WORKDIR /workspaces

# Personalizar Bash e Vim para uma experiência mais agradável
RUN echo 'export PS1="\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "' >> /root/.bashrc && \
    echo "alias ll='ls -ltra'" >> /root/.bashrc && \
    echo "alias ls='ls --color=auto'" >> /root/.bashrc && \
    echo "alias grep='grep --color=auto'" >> /root/.bashrc && \
    echo "export TERM=xterm-256color" >> /root/.bashrc && \
    printf "syntax on\nset number\nset mouse=a\nset background=dark\nset laststatus=2\n" > /root/.vimrc

# Default command
CMD ["bash"]
