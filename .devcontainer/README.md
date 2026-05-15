Resumo do Progresso — Preparação do .devcontainer com Índice FAISS Pré-construído
      📋 Contexto
      O objetivo é deixar a pasta .devcontainer pronta para que qualquer pessoa — inclusive não-técnicos — consiga rodar o projeto no GitHub
      Codespaces sem precisar construir o índice FAISS localmente. Para isso, o índice será construído aqui no desktop (com GPU RTX3090) e
      commitado no repositório, de modo que o Codespaces apenas faça a busca (retrieval) sem a etapa pesada de indexação.

      **Pré-requisito:** Git LFS (Large File Storage) deve estar instalado e inicializado no repositório antes de qualquer commit com os arquivos do índice FAISS.
      Sem isso, o GitHub rejeitará o push por exceder o limite de tamanho de arquivo (100 MB).

      - Instalação: https://git-lfs.com/
      - Após instalar, execute no repositório: `git lfs install`
      - Rastreie os arquivos: `git lfs track "faiss_index/**"`
      - Confirme com: `git lfs ls-files` (deve listar `index.faiss` e `index.pkl`)

      🔍 Análise Realizada

      1. Estrutura do .devcontainer examinada
         - devcontainer.json: configura nome, portas (8501, 8888), extensões VSCode, variáveis de ambiente (CHATFGV_INDEX, CHATFGV_DHBB) e
         postCreateCommand que executa setup.sh.
         - Dockerfile: baseado em rocker/r-ver:4.4.2, instala dependências do sistema, Python packages (incluindo faiss-cpu e torch==2.5.1+cpu), e
         copia os arquivos do projeto.
         - setup.sh: constrói o índice FAISS se não existir, configura aliases e cria arquivo de status.

      2. Código de indexação (dhbb-query.py)
         - Usa HuggingFaceEmbeddings com modelo PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir
         - Chunking com RecursiveCharacterTextSplitter (2000/100)
         - Salva índice em /workspaces/ChatFGV/faiss_index com FAISS.from_documents(...).save_local()
         - Busca via FAISS.load_local() e similarity_search()

      3. Dados
         - 7.863 arquivos .text no diretório DHBB/text (~88 MB)
         - O índice FAISS já está commitado no repositório (com LFS ativo)
         - O .gitignore NÃO contém .faiss nem .pkl (removido para permitir o commit)
⚙️ Ações Executadas

      1. Criado ambiente local com GPU
         - Utilizado uv para criar venv com Python 3.12
         - Instalado torch com CUDA 12.1 (compatível com RTX3090): torch-2.5.1+cu121
         - Instaladas dependências: sentence-transformers, faiss-cpu, langchain, langchain-community, langchain-core, langchain-text-splitters, pyyaml, tqdm

      2. GPU verificada
         ```
         CUDA available: True
         CUDA version: 12.1
         Device: NVIDIA GeForce RTX 3090
         ```

      3. Indexação concluída
         - 7.863 verbetes carregados
         - 38.362 chunks gerados
         - Tempo total de indexação: ~10 min (com GPU RTX3090)
         - Aviso de depreciação do HuggingFaceEmbeddings (não crítico)

      4. .gitignore ajustado
         - Removidas as linhas .pkl e .faiss do .gitignore
         - O índice agora pode ser commitado

      5. Git LFS configurado
         - `git lfs install` — inicializa hooks LFS
         - `git lfs track "faiss_index/**"` — rastreia arquivos grandes
         - `git lfs migrate import` — reescreve histórico convertendo binários em ponteiros LFS
         - `git push --force` — envia com objetos LFS

      📊 Status Atual

      | Item                                     | Estado                             |
      |------------------------------------------|------------------------------------|
      | Ambiente venv (Python 3.12 + torch CUDA) | ✅ Pronto                          |
      | Verbetes DHBB carregados                 | ✅ 7.863                           |
      | Chunks gerados                           | ✅ 38.362                          |
      | Construção do índice FAISS               | ✅ Concluído (225 MB + 68 MB)      |
      | .gitignore (permitindo .faiss)           | ✅ Atualizado                      |
      | Git LFS ativo                            | ✅ Com migração de histórico       |

      🎯 Comandos de Indexação (Reconstruir o índice)

      **Windows (PowerShell):**
      ```powershell
      # Ativar variáveis de ambiente
      $env:CHATFGV_INDEX="C:\caminho\para\faiss_index"
      $env:CHATFGV_DHBB="C:\caminho\para\DHBB\text"

      # Reconstruir o índice
      .venv-index\Scripts\python.exe dhbb-query.py --build-index
      ```

      **Linux / macOS (Bash):**
      ```bash
      # Ativar variáveis de ambiente
      export CHATFGV_INDEX="/caminho/para/faiss_index"
      export CHATFGV_DHBB="/caminho/para/DHBB/text"

      # Reconstruir o índice
      .venv-index/bin/python dhbb-query.py --build-index
      ```

      **Após a indexação — commit e push via LFS:**
      ```bash
      # 1. Adicionar arquivos
      git add faiss_index/index.faiss faiss_index/index.pkl .gitattributes

      # 2. Commitar
      git commit -m "feat: reconstruir índice FAISS (7.863 verbetes, 38.362 chunks, Serafim 900M)"

      # 3. Migrar histórico para LFS (converte binários em ponteiros)
      git lfs migrate import --include="faiss_index/index.faiss,faiss_index/index.pkl"

      # 4. Force push (necessário pois o histórico foi reescrito)
      git push --force

      # 5. Confirmar que LFS está rastreando
      git lfs ls-files
      ```

      ⚠️ **Importante:** Se o erro `GH001: Large files detected` ocorrer, significa que os arquivos grandes ainda existem no histórico sem LFS. A sequência acima (commit → migrate → force push) resolve esse problema.

      📝 Observações

      - Modelo de embedding: PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir (otimizado para português, ~900M parâmetros). Primeira execução baixa o modelo (~800 MB) do Hugging Face.
      - GPU utilizada: A indexação roda com CUDA 12.1 no RTX3090, acelerando significativamente vs CPU-only.
      - Tamanho do índice: `index.faiss` (~225 MB) + `index.pkl` (~68 MB) = ~293 MB no total, rastreados via Git LFS.
      - O warning de depreciação do `HuggingFaceEmbeddings` pode ser resolvido no futuro trocando para `langchain-huggingface`.
      - Comandos úteis:
        - `dhbb "pergunta"` → texto formatado
        - `dhbb --json "pergunta"` → JSON para Copilot Code
        - `chatfgv-streamlit` → interface web
        - `chatfgv-status` → status do sistema
      - Para reindexar no Codespaces (sem GPU), o `setup.sh` detecta automaticamente se o índice já existe e pula a construção.

      📥 Como baixar os arquivos LFS após `git pull`

      Quando você executa `git pull`, apenas os **ponteiros LFS** são baixados (pequenos arquivos de texto). Os arquivos reais (`index.faiss`, `index.pkl`) **não são baixados automaticamente**.

      Para baixar os arquivos reais, execute:

      ```bash
      # Baixar todos os arquivos LFS no repositório
      git lfs pull
      
      # Ou baixar apenas os arquivos do faiss_index
      git lfs pull --include="faiss_index/**"
      ```

      Verifique se os arquivos estão disponíveis:
      ```bash
      ls -la faiss_index/
      # Deve mostrar index.faiss (~225 MB) e index.pkl (~68 MB)
      ```

      Se `git lfs pull` retornar erro "LFS is not installed", instale primeiro com `git lfs install`.