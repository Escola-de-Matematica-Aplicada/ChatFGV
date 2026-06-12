# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a Docker-based development environment running Python 3.11 with multiple AI CLI agents and data science tools. It provides an isolated, reproducible workspace with pre-configured tools for working with Claude, Mistral, Hermes, Kimi, Grok, and other AI platforms, plus a complete data science stack.

## Architecture

**Single Service:**
- **agents**: Python 3.11 slim container with:
  - CLI agents: Claude, Hermes Agent, Kilo Code, Kimi, Vibe (Mistral), Grok CLI
  - Data science stack: Polars, Pandas, NumPy, SciPy, Scikit-learn, Plotly, ClickHouse
  - Development tools: Git, Git LFS, Node.js, ripgrep, FFmpeg, build-essential
  - Workspace mounted at `/workspaces` (maps to current directory)
  - Portuguese (Brazil) locale configured as default

**Key Configuration:**
- Build context: Current directory (builds from local Dockerfile)
- Working directory: `/workspaces` (synced with `.`)
- Locale: `pt_BR.UTF-8`
- No GPU or external service dependencies

## Common Commands

**Start the development container:**
```bash
docker compose up -d
# or run interactively:
docker compose run --rm agents bash
```

Para acesar o modelo Docker model:
`http://host.docker.internal:12434/v1`

Alguns detalhes do Docker hub models:

(ou 65536 / 131072 se tiver VRAM suficiente; Gemma4 suporta até 256k+)

docker model configure --context-size 262144 docker.io/qwen3.5:35B-A3B-Q4_K_M
docker model configure --context-size 262144 docker.io/gemma4:26B
docker model configure --context-size 262144 docker.io/gemma4:latest
docker model configure --context-size 262144 docker.io/gemma4:31B

--> para limpar a GPU
docker model unload --all
--> para ver os modelos carregados
docker model list
--> para carregar um modelo (ao chamar esse sobe sozinho)
docker model run -d gemma4:26B
docker model run -d llama3.1:8B-Q4_K_M
docker model run -d qwen3.5:9B-UD-Q4_K_XL


## Como fazer para usar em outra pasta de trabalho?

Levar para o outro repo, numa subpasta ".agente-local":
- docker-compose.yml
- .env
- .gitignore
- Dockerfile
- CLAUDE.md

Editar o docker-compose.yml para "working_dir" seja a sua nova pasta.

**Access the container shell:**
```bash
docker compose exec agents bash
```

**Run Python commands inside the container:**
```bash
# Single command
docker compose exec agents python3 -c "import polars; print(polars.__version__)"

# Script
docker compose exec agents python3 << 'EOF'
import polars as pl
df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
print(df)
EOF
```

**Run an AI agent from inside the container:**
```bash
docker compose exec agents claude --help
docker compose exec agents hermes-agent --version
```

**Stop and clean up:**
```bash
docker compose down
# Remove images and volumes:
docker compose down --rmi all --volumes
```

**Rebuild the image after Dockerfile changes:**
```bash
docker compose build --no-cache
```

**View container logs:**
```bash
docker compose logs -f agents
```

## Development Notes

**Build Details:**
- Base image: `python:3.11-slim` (optimized for size and performance)
- CLI agents installed via official install scripts at build time
- System dependencies include build tools, git, curl, vim, ripgrep, ffmpeg, and Node.js
- `uv` package manager installed (faster pip alternative)
- MarkItDown library cloned and installed from GitHub

**Workspace:**
- Current directory mounts as `/workspaces` in the container
- All changes made inside the container to `/workspaces` are reflected locally
- Python packages installed with `--break-system-packages` to avoid conflicts with container system packages

**AI Agents Available:**
- **Claude**: Anthropic's CLI for Claude models
- **Hermes Agent**: Nous Research agent framework
- **Kilo Code**: Code generation and analysis agent
- **Kimi**: Moonshot AI agent
- **Vibe (Mistral)**: Mistral AI command-line tool
- **Grok CLI**: X/Grok agent (installed via npm)
- **MarkItDown**: Microsoft tool for markdown conversion (pre-installed in `/opt/markitdown`)

**Data Science Stack:**
- Core: Polars, Pandas, NumPy, SciPy, Scikit-learn
- Visualization: Matplotlib, Seaborn, Plotly
- Data formats: PyArrow
- Analytics: ClickHouse driver and client
- REPL: Radian (enhanced Python REPL)
- Additional: Stemgraphic (statistical graphics)

**Shell Customization:**
The container includes custom bash aliases and vim configuration:
- `ll` → `ls -ltra` (detailed listing)
- `ls` and `grep` with `--color=auto`
- 256-color terminal support
- Vim syntax highlighting, line numbers, mouse support

## Important Notes

**No External Services:**
Unlike previous iterations of this project, there are no Ollama or vLLM services. This is a self-contained development environment. AI model access is provided through the installed CLI agents (e.g., `claude`, `hermes-agent`), which may connect to external APIs based on configuration.

**Volume Mounting:**
The entire repository is mounted at `/workspaces`. Any files created or modified inside the container are immediately visible on the host filesystem.

**Security:**
- The `.env` file may contain API tokens or credentials and should **never be committed** to the repository
- Ensure `.gitignore` includes `.env` and any local configuration files
- Install agents from official sources (install scripts pinned in Dockerfile)

**Performance:**
- First build may take 10-15 minutes due to agent installation scripts and package downloads
- Subsequent builds are faster due to Docker layer caching
- Container startup is near-instantaneous once the image is built
