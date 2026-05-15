#!/usr/bin/env python3
"""
dhbb-query.py - CLI autonoma para recuperar contexto do DHBB via FAISS

Sem dependencia de Ollama ou LLM local. Esta ferramenta faz APENAS
a busca semantica no indice FAISS e retorna os documentos relevantes
com suas fontes.

A geracao da resposta e feita pelo GitHub Copilot Chat, que le a
saida deste script e formula a resposta em portugues.

Uso:
  python3 dhbb-query.py "Quem foi Getulio Vargas?"
  python3 dhbb-query.py --json "Qual foi o papel de Juscelino Kubitschek?"
  python3 dhbb-query.py --top-k 3 "O que foi a Revolucao de 1930?"
  python3 dhbb-query.py --check
  python3 dhbb-query.py --build-index

Saida (modo texto):
  Documentos relevantes do DHBB, com indicacao das fontes.

Saida (modo --json):
  {"contexto": "...", "fontes": [...], "num_docs": N, "tempo_s": N}
"""

import argparse
import json
import os
import sys
import time

# ============================================================
# Configuracao via variaveis de ambiente (com padroes)
# ============================================================
INDEX_PATH = os.environ.get("CHATFGV_INDEX", "/workspaces/ChatFGV/faiss_index")
DHBB_PATH = os.environ.get("CHATFGV_DHBB", "/workspaces/ChatFGV/DHBB/text")
EMBEDDING_MODEL = "PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 100


# ============================================================
# Verificacoes de sistema
# ============================================================
def check_faiss_index():
    """Verifica se o indice FAISS existe."""
    return os.path.isdir(INDEX_PATH) and os.path.isfile(os.path.join(INDEX_PATH, "index.faiss"))


def check_system():
    """Verifica se o sistema esta configurado corretamente."""
    faiss_ok = check_faiss_index()
    embeddings_ok = True
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
    except ImportError:
        embeddings_ok = False

    status = {
        "faiss_index": "OK" if faiss_ok else "NAO_ENCONTRADO",
        "embeddings": "OK" if embeddings_ok else "NAO_INSTALADO",
        "index_path": INDEX_PATH,
        "dhbb_path": DHBB_PATH,
        "embedding_model": EMBEDDING_MODEL,
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return faiss_ok and embeddings_ok


# ============================================================
# Construcao do indice FAISS
# ============================================================
def build_index():
    """Constroi o indice FAISS a partir dos verbetes do DHBB."""
    import glob
    import yaml
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document

    text_files = glob.glob(os.path.join(DHBB_PATH, "**/*.text"), recursive=True)
    if not text_files:
        raise ValueError(f"Nenhum arquivo .text encontrado em {DHBB_PATH}")

    documents = []
    for file_path in text_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                metadata = {}
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            metadata = yaml.safe_load(parts[1]) or {}
                        except Exception:
                            pass
                metadata["source"] = os.path.basename(file_path)
                metadata["file_path"] = file_path
                documents.append(Document(page_content=content, metadata=metadata))
        except Exception as e:
            print(f"Aviso: erro ao processar {file_path}: {e}", file=sys.stderr)

    print(f"  {len(documents)} verbetes carregados", file=sys.stderr)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    docs = text_splitter.split_documents(documents)
    print(f"  {len(docs)} chunks gerados", file=sys.stderr)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(documents=docs, embedding=embeddings)
    vectorstore.save_local(INDEX_PATH)
    print(f"  Indice salvo em {INDEX_PATH}", file=sys.stderr)
    return vectorstore


# ============================================================
# Busca no DHBB - Apenas recuperacao, sem geracao
# ============================================================
def search_dhbb(question, top_k=2, json_output=False):
    """
    Busca documentos relevantes no DHBB para a pergunta dada.

    Args:
        question: A pergunta em portugues
        top_k: Numero de documentos a recuperar (padrao: 2)
        json_output: Se True, retorna JSON em vez de texto formatado

    Returns:
        Resultado formatado (texto ou JSON) com contexto e fontes.
        NAO gera resposta - isso e feito pelo Copilot Chat.
    """
    start_time = time.time()

    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    # Carregar indice FAISS
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        INDEX_PATH, embeddings, allow_dangerous_deserialization=True
    )

    # Buscar documentos relevantes
    docs = vectorstore.similarity_search(question, k=top_k)

    # Extrair fontes e montar contexto
    sources = []
    context_parts = []
    for doc in docs:
        source = doc.metadata.get("source", "Fonte desconhecida")
        if source not in sources:
            sources.append(source)
        context_parts.append(doc.page_content)

    context = "\n\n---\n\n".join(context_parts)
    elapsed = round(time.time() - start_time, 2)

    if json_output:
        return json.dumps({
            "contexto": context,
            "fontes": sources,
            "num_docs": len(docs),
            "tempo_s": elapsed,
            "top_k": top_k
        }, ensure_ascii=False, indent=2)
    else:
        lines = [
            "==================================================",
            f"  ChatFGV - Resultados da busca no DHBB",
            f"  Pergunta: {question}",
            f"  Documentos encontrados: {len(docs)}",
            f"  Tempo de busca: {elapsed}s",
            "==================================================",
            "",
            context,
            "",
            "==================================================",
        ]
        if sources:
            if len(sources) == 1:
                lines.append(f"  Fonte: {sources[0]}")
            else:
                lines.append(f"  Fontes: {', '.join(sources)}")
        lines.append("==================================================")
        return "\n".join(lines)


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="ChatFGV - Buscar contexto no DHBB via FAISS (sem LLM local)",
        epilog="Exemplo: dhbb-query.py 'Quem foi Getulio Vargas?'"
    )
    parser.add_argument(
        "question", nargs="?", default=None,
        help="Pergunta sobre o DHBB"
    )
    parser.add_argument(
        "--top-k", type=int, default=2,
        help="Numero de documentos a recuperar (padrao: 2)"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Saida em formato JSON (para uso pelo Copilot Code)"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Verificar se o sistema esta configurado"
    )
    parser.add_argument(
        "--build-index", action="store_true",
        help="(Re)construir o indice FAISS"
    )

    args = parser.parse_args()

    # Modo de verificacao
    if args.check:
        ok = check_system()
        sys.exit(0 if ok else 1)

    # (Re)construir indice
    if args.build_index:
        print("Construindo indice FAISS...", file=sys.stderr)
        build_index()
        print("Indice construido com sucesso!", file=sys.stderr)
        sys.exit(0)

    # Requer pergunta
    if not args.question:
        parser.print_help()
        sys.exit(1)

    # Verificar indice
    if not check_faiss_index():
        print(f"ERRO: Indice FAISS nao encontrado em {INDEX_PATH}", file=sys.stderr)
        print("Execute: python3 dhbb-query.py --build-index", file=sys.stderr)
        sys.exit(1)

    try:
        result = search_dhbb(
            question=args.question,
            top_k=args.top_k,
            json_output=args.json_output
        )
        print(result)
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
