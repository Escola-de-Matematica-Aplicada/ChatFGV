#!/usr/bin/env bash
set -uo pipefail

# ============================================================
# ChatFGV - Post-Create Setup para GitHub Codespaces
# ============================================================
# Este script e executado automaticamente apos a criacao do
# container. Constroi o indice FAISS do DHBB e configura
# aliases para consulta rapida.
#
# NAO ha Ollama ou LLM local - a geracao de respostas
# e feita pelo proprio GitHub Copilot Chat.
# ============================================================

# Log file for debugging setup failures
SETUP_LOG="/workspaces/ChatFGV/.setup.log"
exec > >(tee -a "$SETUP_LOG") 2>&1

echo ""
echo "============================================================"
echo "  ChatFGV - Configurando ambiente RAG para DHBB"
echo "============================================================"
echo ""

# Ensure ~/.local/bin is on PATH
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$HOME/.local/bin"; then
  if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
  fi
  export PATH="$HOME/.local/bin:$PATH"
fi

# ============================================================
# 1. CONSTRUIR INDICE FAISS
# ============================================================
echo "[1/3] Construindo indice FAISS do DHBB..."

INDEX_PATH="${CHATFGV_INDEX:-/workspaces/ChatFGV/faiss_index}"
DHBB_PATH="${CHATFGV_DHBB:-/workspaces/ChatFGV/DHBB/text}"
CLI_SCRIPT="/workspaces/ChatFGV/dhbb-query.py"

if [ -d "$INDEX_PATH" ] && [ -f "$INDEX_PATH/index.faiss" ]; then
  echo "  Indice FAISS ja existe em: $INDEX_PATH"
  INDEX_SIZE=$(du -sh "$INDEX_PATH" | cut -f1)
  echo "  Tamanho: $INDEX_SIZE"
else
  echo "  Construindo indice com Serafim (pode levar 30-60 minutos)..."
  echo "  Verbetes: $(ls "$DHBB_PATH"/*.text 2>/dev/null | wc -l) arquivos"

  cd /workspaces/ChatFGV

  # Run with unbuffered output so logs are visible in real-time
  if PYTHONUNBUFFERED=1 python3 dhbb-query.py --build-index 2>&1; then
    echo "  Indice construido com sucesso!"
    INDEX_SIZE=$(du -sh "$INDEX_PATH" | cut -f1)
    echo "  Tamanho: $INDEX_SIZE"
  else
    echo "  ERRO: Falha ao construir indice FAISS"
    echo "  O indice sera reconstruido manualmente com:"
    echo "    python3 dhbb-query.py --build-index"
  fi
fi

# ============================================================
# 2. VERIFICAR SCRIPT CLI
# ============================================================
echo "[2/3] Verificando script CLI de consulta..."

if [ -f "$CLI_SCRIPT" ]; then
  echo "  Script CLI encontrado: $CLI_SCRIPT"
  echo "  Testando --check..."
  python3 "$CLI_SCRIPT" --check 2>/dev/null || echo "  (check parcial - alguns componentes podem nao estar prontos)"
else
  echo "  AVISO: Script CLI nao encontrado em $CLI_SCRIPT"
fi

# ============================================================
# 3. CONFIGURACAO FINAL
# ============================================================
echo "[3/3] Configuracoes finais..."

# Criar alias para consulta rapida
if ! grep -q "alias dhbb=" "$HOME/.bashrc" 2>/dev/null; then
  cat >> "$HOME/.bashrc" << 'EOF'

# ============================================================
# ChatFGV - Aliases para consulta rapida ao DHBB
# ============================================================
alias dhbb='python3 /workspaces/ChatFGV/dhbb-query.py'
alias chatfgv-streamlit='cd /workspaces/ChatFGV/RAG-streamlit-api && streamlit run app.py'
alias chatfgv-status='echo "=== FAISS ===" && (ls -la /workspaces/ChatFGV/faiss_index/ 2>/dev/null || echo "Indice nao encontrado") && echo "" && python3 /workspaces/ChatFGV/dhbb-query.py --check'
EOF
  echo "  Aliases adicionados: dhbb, chatfgv-streamlit, chatfgv-status"
fi

# Criar arquivo de status para Copilot Code
cat > /workspaces/ChatFGV/.chatfgv-status << EOF
{
  "status": "ready",
  "faiss_index": "$INDEX_PATH",
  "dhbb_texts": "$DHBB_PATH",
  "cli_script": "$CLI_SCRIPT",
  "embedding_model": "PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir",
  "streamlit_port": 8501,
  "generation": "GitHub Copilot Chat (sem LLM local)",
  "setup_completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo ""
echo "============================================================"
echo "  ChatFGV - Ambiente Pronto!"
echo "============================================================"
echo ""
echo "  Para fazer perguntas ao DHBB:"
echo ""
echo "  Via Copilot Code:"
echo "    Basta perguntar no chat! Exemplo:"
echo "    'Quem foi Getulio Vargas?'"
echo "    O Copilot buscara o contexto no DHBB e gerara a resposta."
echo ""
echo "  Via terminal (apenas busca):"
echo "    dhbb 'Quem foi Getulio Vargas?'"
echo "    dhbb --json 'Quem foi Getulio Vargas?'"
echo ""
echo "  Via interface web (Streamlit):"
echo "    chatfgv-streamlit"
echo "    Acesse a porta 8501 no browser"
echo ""
echo "  Verificar status:"
echo "    chatfgv-status"
echo ""
echo "============================================================"
