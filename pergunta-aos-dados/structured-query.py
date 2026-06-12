#!/usr/bin/env python3
"""
structured-query.py - CLI autonoma para bases de dados estruturadas.
Combina busca semântica no dicionário de dados (FAISS) com consultas SQL (PostgreSQL).

Sem dependencia de Ollama ou LLM local. Esta ferramenta:
1. Busca o dicionário de dados relevante via FAISS
2. Gera SQL a partir da pergunta
3. Executa o SQL no PostgreSQL
4. Retorna os resultados

A geracao da resposta final e feita pelo GitHub Copilot Chat.

Uso:
  python3 structured-query.py "Quantos acidentes houve em SP em 2024?"
  python3 structured-query.py --json "Qual UF tem mais acidentes?"
  python3 structured-query.py --check
  python3 structured-query.py --build-index
  python3 structured-query.py --schema
  python3 structured-query.py --list-tables
"""

import argparse
import json
import os
import sys
import time

# ============================================================
# Configuracao
# ============================================================
STRUCTURED_INDEX_PATH = os.environ.get(
    "STRUCTURED_INDEX_PATH",
    "/workspaces/pergunta-aos-dados/structured_faiss_index"
)
DICIONARIO_TEXTO_PATH = os.environ.get(
    "DICIONARIO_TEXTO_PATH",
    "/workspaces/pergunta-aos-dados/Bases-de-Dados/dicionario_texto.txt"
)
DICIONARIO_JSON_PATH = os.environ.get(
    "DICIONARIO_JSON_PATH",
    "/workspaces/pergunta-aos-dados/Bases-de-Dados/dicionario_texto.json"
)
EMBEDDING_MODEL = "PORTULAN/serafim-900m-portuguese-pt-sentence-encoder-ir"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 100

DB_CONFIG = {
    "dbname": os.environ.get("STRUCTURED_DB", "postgres"),
    "user": os.environ.get("STRUCTURED_USER", "postgres"),
    "password": os.environ.get("STRUCTURED_PASSWORD", "postgres"),
    "host": os.environ.get("STRUCTURED_HOST", "localhost"),
    "port": os.environ.get("STRUCTURED_PORT", "5432"),
}

# Mapeamento de tabelas e descrições
TABELAS_INFO = {
    "acidentes_transito": {
        "descricao": "Acidentes de trânsito em rodovias federais (DNIT/DataTran, 2024)",
        "periodo": "2024",
        "registros": 73156,
        "colunas_desc": {
            "id": "ID do acidente",
            "data_inversa": "Data (AAAA-MM-DD)",
            "dia_semana": "Dia da semana",
            "horario": "Horário",
            "uf": "UF (sigla)",
            "br": "Rodovia federal (ex: 101 = BR-101)",
            "km": "Quilômetro",
            "municipio": "Município",
            "causa_acidente": "Causa do acidente",
            "tipo_acidente": "Tipo de colisão",
            "classificacao_acidente": "Classificação (Sem Vítimas, Com Vítimas, etc.)",
            "fase_dia": "Fase do dia",
            "sentido_via": "Sentido da via",
            "condicao_metereologica": "Condição climática",
            "tipo_pista": "Tipo de pista",
            "tracado_via": "Traçado",
            "uso_solo": "Uso de solo",
            "pessoas": "Total de pessoas",
            "mortos": "Número de mortos",
            "feridos_leves": "Feridos leves",
            "feridos_graves": "Feridos graves",
            "ileso": "Ilesos",
            "ignorados": "Ignorados",
            "feridos": "Total de feridos",
            "veiculos": "Veículos envolvidos",
            "latitude": "Latitude",
            "longitude": "Longitude",
            "regional": "Regional DNIT",
            "delegacia": "Delegacia",
            "uop": "Unidade Operacional",
        },
        "tipos_pergunta": [
            "acidente", "colisao", "rodovia", "fatal", "morte", "mortes",
            "ferido", "ferimentos", "km", "quilometro", "br-", "uf", "estado",
            "municipio", "causa", "clima", "chuva", "noite", "madrugada",
            "dnit", "datatran", "infraestrutura", "transito", "trafego"
        ]
    },
    "censo_setores": {
        "descricao": "Estrutura geográfica dos setores censitários (IBGE Censo 2022)",
        "periodo": "2022",
        "registros": 468099,
        "colunas_desc": {
            "cd_setor": "Código do setor censitário (chave primária)",
            "situacao": "Situação (Urbana/Rural)",
            "cd_sit": "Código da situação",
            "cd_tipo": "Código do tipo",
            "area_km2": "Área em km²",
            "cd_regiao": "Código da região",
            "nm_regiao": "Nome da região (Norte, Nordeste, etc.)",
            "cd_uf": "Código da UF",
            "nm_uf": "Nome da UF",
            "cd_mun": "Código do município",
            "nm_mun": "Nome do município",
            "cd_dist": "Código do distrito",
            "nm_dist": "Nome do distrito",
            "cd_subdist": "Código do subdistrito",
            "nm_subdist": "Nome do subdistrito",
            "cd_bairro": "Código do bairro",
            "nm_bairro": "Nome do bairro",
            "cd_nu": "Código do núcleo urbano",
            "cd_fcu": "Código da FCU",
            "cd_aglom": "Código do aglomerado",
            "cd_rgint": "Código da região integrada",
            "cd_rgi": "Código da RGI",
            "cd_concurb": "Código da conurbação",
            "v0001": "Total de pessoas",
            "v0002": "Total de Domicílios",
            "v0003": "Domicílios Particulares",
            "v0004": "Domicílios Coletivos",
            "v0005": "Média de moradores por DPO",
            "v0006": "Percentual de DPO imputados",
            "v0007": "Domicílios Particulares Ocupados",
        },
        "tipos_pergunta": [
            "censo", "populacao", "pessoas", "domicilio", "setor",
            "urbana", "rural", "area", "km2", "regiao", "municipio",
            "bairro", "distrito", "ibge", "2022", "demografico"
        ]
    },
    "censo_basico": {
        "descricao": "Indicadores básicos demográficos por setor censitário (IBGE Censo 2022)",
        "periodo": "2022",
        "registros": 468099,
        "colunas_desc": {
            "cd_setor": "Código do setor censitário (chave primária)",
            "situacao": "Situação (Urbana/Rural)",
            "cd_sit": "Código da situação",
            "cd_tipo": "Código do tipo",
            "area_km2": "Área em km²",
            "cd_regiao": "Código da região",
            "nm_regiao": "Nome da região",
            "cd_uf": "Código da UF",
            "nm_uf": "Nome da UF",
            "cd_mun": "Código do município",
            "nm_mun": "Nome do município",
            "cd_dist": "Código do distrito",
            "nm_dist": "Nome do distrito",
            "cd_subdist": "Código do subdistrito",
            "nm_subdist": "Nome do subdistrito",
            "cd_bairro": "Código do bairro",
            "nm_bairro": "Nome do bairro",
            "cd_nu": "Código do núcleo urbano",
            "cd_fcu": "Código da FCU",
            "cd_aglom": "Código do aglomerado",
            "cd_rgint": "Código da região integrada",
            "cd_rgi": "Código da RGI",
            "cd_concurb": "Código da conurbação",
            "v0001": "Total de pessoas",
            "v0002": "Total de Domicílios",
            "v0003": "Domicílios Particulares",
            "v0004": "Domicílios Coletivos",
            "v0005": "Média de moradores por DPO",
            "v0006": "Percentual de DPO imputados",
            "v0007": "Domicílios Particulares Ocupados",
        },
        "tipos_pergunta": [
            "censo", "populacao", "pessoas", "domicilio", "setor",
            "urbana", "rural", "area", "km2", "regiao", "municipio",
            "bairro", "distrito", "ibge", "2022", "basico", "demografico"
        ]
    },
    "censo_alfabetizacao": {
        "descricao": "Dados de alfabetização por setor censitário (IBGE Censo 2022)",
        "periodo": "2022",
        "registros": 458772,
        "colunas_desc": {
            "cd_setor": "Código do setor censitário (chave primária)",
            "situacao": "Situação (Urbana/Rural)",
            "cd_sit": "Código da situação",
            "cd_tipo": "Código do tipo",
            "area_km2": "Área em km²",
            "cd_regiao": "Código da região",
            "nm_regiao": "Nome da região",
            "cd_uf": "Código da UF",
            "nm_uf": "Nome da UF",
            "cd_mun": "Código do município",
            "nm_mun": "Nome do município",
            "cd_dist": "Código do distrito",
            "nm_dist": "Nome do distrito",
            "cd_subdist": "Código do subdistrito",
            "nm_subdist": "Nome do subdistrito",
            "cd_bairro": "Código do bairro",
            "nm_bairro": "Nome do bairro",
            "cd_nu": "Código do núcleo urbano",
            "cd_fcu": "Código da FCU",
            "cd_aglom": "Código do aglomerado",
            "cd_rgint": "Código da região integrada",
            "cd_rgi": "Código da RGI",
            "cd_concurb": "Código da conurbação",
            "v0001": "Total de pessoas",
            "v0002": "Total de Domicílios",
            "v0003": "Domicílios Particulares",
            "v0004": "Domicílios Coletivos",
            "v0005": "Média de moradores por DPO",
            "v0006": "Percentual de DPO imputados",
            "v0007": "Domicílios Particulares Ocupados",
        },
        "tipos_pergunta": [
            "alfabetiza", "leitura", "analfabet", "escolar", "educacao",
            "ensino", "escola", "leitor", "alfabetizado", "alfabetizar"
        ]
    },
    "censo_obitos": {
        "descricao": "Dados de óbitos por setor censitário (IBGE Censo 2022)",
        "periodo": "2022",
        "registros": 458772,
        "colunas_desc": {
            "cd_setor": "Código do setor censitário (chave primária)",
            "situacao": "Situação (Urbana/Rural)",
            "cd_sit": "Código da situação",
            "cd_tipo": "Código do tipo",
            "area_km2": "Área em km²",
            "cd_regiao": "Código da região",
            "nm_regiao": "Nome da região",
            "cd_uf": "Código da UF",
            "nm_uf": "Nome da UF",
            "cd_mun": "Código do município",
            "nm_mun": "Nome do município",
            "cd_dist": "Código do distrito",
            "nm_dist": "Nome do distrito",
            "cd_subdist": "Código do subdistrito",
            "nm_subdist": "Nome do subdistrito",
            "cd_bairro": "Código do bairro",
            "nm_bairro": "Nome do bairro",
            "cd_nu": "Código do núcleo urbano",
            "cd_fcu": "Código da FCU",
            "cd_aglom": "Código do aglomerado",
            "cd_rgint": "Código da região integrada",
            "cd_rgi": "Código da RGI",
            "cd_concurb": "Código da conurbação",
            "v0001": "Total de pessoas",
            "v0002": "Total de Domicílios",
            "v0003": "Domicílios Particulares",
            "v0004": "Domicílios Coletivos",
            "v0005": "Média de moradores por DPO",
            "v0006": "Percentual de DPO imputados",
            "v0007": "Domicílios Particulares Ocupados",
        },
        "tipos_pergunta": [
            "obito", "morte", "mortes", "falec", "biti", "vida",
            "esperanca", "mortalidade", "mortal", "obituario"
        ]
    },
    "contagem_trafego": {
        "descricao": "Contagem de tráfego em rodovias federais (DNIT/CGPLAN - Dez/2020)",
        "periodo": "2020-12",
        "registros": 6769,
        "colunas_desc": {
            "id": "Identificador único do trecho",
            "vl_br": "Rodovia federal (ex: 307 = BR-307)",
            "sg_uf": "UF (sigla)",
            "nm_tipo_tr": "Tipo de trecho",
            "sg_tipo_tr": "Sigla do tipo (B=Eixo, R=Ramal, D=Duplicação)",
            "vl_codigo": "Código completo do trecho",
            "ds_local_i": "Local inicial",
            "ds_local_f": "Local final",
            "vl_km_inic": "KM inicial",
            "vl_km_fina": "KM final",
            "vl_extensa": "Extensão em km",
            "ds_sup_fed": "Natureza da propriedade",
            "classificacao": "Classificação (Planejada, Implantada)",
            "geh": "Índice GEH de qualidade",
            "a_c": "Caminhão (hora pico manhã)",
            "b_c": "Ônibus (hora pico manhã)",
            "c_c": "Caminhonete (hora pico manhã)",
            "d_c": "Veículo Especial (hora pico manhã)",
            "e_c": "Motocicleta (hora pico manhã)",
            "f_c": "Outros (hora pico manhã)",
            "g_c": "Automóvel (hora pico manhã)",
            "h_c": "Trator (hora pico manhã)",
            "i_c": "Reboque (hora pico manhã)",
            "j_c": "Total carga (hora pico manhã)",
            "a_d": "Caminhão (hora pico tarde)",
            "b_d": "Ônibus (hora pico tarde)",
            "c_d": "Caminhonete (hora pico tarde)",
            "d_d": "Veículo Especial (hora pico tarde)",
            "e_d": "Motocicleta (hora pico tarde)",
            "f_d": "Outros (hora pico tarde)",
            "g_d": "Automóvel (hora pico tarde)",
            "h_d": "Trator (hora pico tarde)",
            "i_d": "Reboque (hora pico tarde)",
            "j_d": "Total carga (hora pico tarde)",
            "vmda_c": "Volume Médio Diário manhã",
            "vmda_d": "Volume Médio Diário tarde",
            "ns_c": "Amostras manhã",
            "ns_d": "Amostras tarde",
        },
        "tipos_pergunta": [
            "trafego", "veiculo", "carro", "automovel", "caminhao",
            "onibus", "moto", "rodovia", "br-", "km", "volume",
            "fluxo", "contagem", "vlmd", "vmd", "geH"
        ]
    }
}


# ============================================================
# Verificacoes de sistema
# ============================================================
def verificar_postgres():
    """Verificar conexão com PostgreSQL."""
    try:
        import psycopg2
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        return True
    except Exception as e:
        print(f"ERRO: PostgreSQL não acessível: {e}")
        return False


def check_faiss_index():
    """Verifica se o indice FAISS existe."""
    return os.path.isdir(STRUCTURED_INDEX_PATH) and os.path.isfile(
        os.path.join(STRUCTURED_INDEX_PATH, "index.faiss")
    )


def check_system():
    """Verifica se o sistema esta configurado corretamente."""
    faiss_ok = check_faiss_index()
    pg_ok = verificar_postgres()
    embeddings_ok = True
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401
    except ImportError:
        embeddings_ok = False

    status = {
        "faiss_index": "OK" if faiss_ok else "NAO_ENCONTRADO",
        "postgres": "OK" if pg_ok else "NAO_CONECTADO",
        "embeddings": "OK" if embeddings_ok else "NAO_INSTALADO",
        "index_path": STRUCTURED_INDEX_PATH,
        "host": DB_CONFIG["host"],
        "port": DB_CONFIG["port"],
        "dbname": DB_CONFIG["dbname"],
        "tabelas_disponiveis": list(TABELAS_INFO.keys()),
        "num_tabelas": len(TABELAS_INFO),
    }
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return faiss_ok and pg_ok and embeddings_ok


# ============================================================
# Construcao do indice FAISS
# ============================================================
def build_index():
    """Constroi o indice FAISS a partir do dicionario de dados."""
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document

    if not os.path.exists(DICIONARIO_JSON_PATH):
        print(f"ERRO: {DICIONARIO_JSON_PATH} nao encontrado.", file=sys.stderr)
        print("Execute: python3 Bases-de-Dados/gerar_texto_dicionario.py", file=sys.stderr)
        sys.exit(1)

    # Carregar chunks do JSON
    with open(DICIONARIO_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []
    for chunk in data['chunks']:
        documents.append(Document(
            page_content=chunk['texto'],
            metadata={"source": "dicionario_texto", "chunk_id": chunk['id']}
        ))

    print(f"  {len(documents)} chunks carregados", file=sys.stderr)

    # Split em chunks menores se necessario
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    docs = text_splitter.split_documents(documents)
    print(f"  {len(docs)} chunks apos splitting", file=sys.stderr)

    # Embedding
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.from_documents(documents=docs, embedding=embeddings)
    vectorstore.save_local(STRUCTURED_INDEX_PATH)
    print(f"  Indice salvo em {STRUCTURED_INDEX_PATH}", file=sys.stderr)
    return vectorstore


# ============================================================
# Busca no dicionario de dados
# ============================================================
def search_dicionario(question, top_k=2):
    """Buscar no dicionário de dados via FAISS."""
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vectorstore = FAISS.load_local(
        STRUCTURED_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
    )

    docs = vectorstore.similarity_search(question, k=top_k)
    return docs


# ============================================================
# Geracao de SQL
# ============================================================
def gerar_sql(pergunta):
    """
    Gerar SQL a partir da pergunta em linguagem natural.
    Usa heurísticas baseadas no vocabulário da pergunta.
    """
    pergunta_baixa = pergunta.lower()

    # Determinar qual tabela usar
    tabelas_usadas = []
    for nome, info in TABELAS_INFO.items():
        for termo in info['tipos_pergunta']:
            if termo in pergunta_baixa:
                tabelas_usadas.append(nome)
                break

    # Se nenhuma tabela foi encontrada, sugerir as mais relevantes
    if not tabelas_usadas:
        if any(termo in pergunta_baixa for termo in ['quant', 'total', 'numero', 'conto', 'mu', 'muit', 'pouq']):
            tabelas_usadas = list(TABELAS_INFO.keys())[:3]
        elif 'uf' in pergunta_baixa or 'estado' in pergunta_baixa or any(uf in pergunta_baixa for uf in [' sp ', ' rj ', ' mg ', ' ba ', ' rs ', ' pr ', ' sc ', ' go ', ' ce ', ' pa ', ' am ', ' pe ', ' rn ', ' pb ', ' al ', ' df ', ' ma ', ' pi ', ' se ', ' mt ', ' to ', ' ac ', ' ap ', ' ro ']):
            tabelas_usadas = ['acidentes_transito', 'contagem_trafego', 'censo_setores']
        else:
            tabelas_usadas = list(TABELAS_INFO.keys())

    # Detectar ações e agregações
    has_count = any(termo in pergunta_baixa for termo in ['quant', 'total', 'numero', 'conto', 'mu', 'muit', 'pouq'])
    has_group = any(termo in pergunta_baixa for termo in ['por', 'cada', 'separa', 'dividi', 'agrupa', 'orden', 'classifi', 'rank'])
    has_top = any(termo in pergunta_baixa for termo in ['mais', 'menos', 'primei', 'ultim', 'top', 'maior', 'menor', 'maiores', 'menores'])
    has_order = any(termo in pergunta_baixa for termo in ['orden', 'classifi', 'rank', 'maior', 'menor', 'cresce', 'decresce'])
    has_limit = any(termo in pergunta_baixa for termo in ['top 5', 'top 10', 'top 20', 'primei', 'ultim', 'limite'])

    limit_val = 10
    if has_top:
        if 'top 5' in pergunta_baixa:
            limit_val = 5
        elif 'top 10' in pergunta_baixa:
            limit_val = 10
        elif 'top 20' in pergunta_baixa:
            limit_val = 20
        elif 'primei' in pergunta_baixa or 'ultim' in pergunta_baixa:
            limit_val = 5

    # Detectar período
    has_date = '202' in pergunta_baixa

    # Detectar UF
    has_uf = any(uf in pergunta_baixa for uf in [' sp ', ' rj ', ' mg ', ' ba ', ' rs ', ' pr ', ' sc ', ' go ', ' ce ', ' pa ', ' am ', ' pe ', ' rn ', ' pb ', ' al ', ' df ', ' ma ', ' pi ', ' se ', ' mt ', ' to ', ' ac ', ' ap ', ' ro '])

    # Construir SQL para cada tabela
    resultados = []
    for tname in tabelas_usadas:
        sql = construir_sql(tname, pergunta, pergunta_baixa, has_count, has_group, has_top, has_order, has_limit, limit_val, has_date, has_uf)
        if sql:
            resultados.append((tname, sql))

    return resultados


def construir_sql(tname, pergunta, pergunta_baixa, has_count, has_group, has_top, has_order, has_limit, limit_val, has_date, has_uf):
    """Construir SQL específico para uma tabela."""
    if tname not in TABELAS_INFO:
        return None

    info = TABELAS_INFO[tname]
    colunas = list(info['colunas_desc'].keys())

    sql_parts = []

    # SELECT
    if has_count:
        if has_group:
            # Detectar grupo
            group_col = colunas[0]
            if 'uf' in pergunta_baixa or 'estado' in pergunta_baixa or 'unidade federativa' in pergunta_baixa:
                for c in ['nm_uf', 'sg_uf', 'cd_uf', 'uf']:
                    if c in colunas:
                        group_col = c
                        break
            elif 'regiao' in pergunta_baixa or 'região' in pergunta_baixa:
                for c in ['nm_regiao', 'cd_regiao', 'nm_regiao']:
                    if c in colunas:
                        group_col = c
                        break
            elif 'municipio' in pergunta_baixa or 'município' in pergunta_baixa:
                for c in ['nm_mun', 'cd_mun']:
                    if c in colunas:
                        group_col = c
                        break
            elif 'br' in pergunta_baixa or 'rodovia' in pergunta_baixa:
                for c in ['vl_br', 'br']:
                    if c in colunas:
                        group_col = c
                        break
            elif 'causa' in pergunta_baixa or 'tipo' in pergunta_baixa:
                for c in ['causa_acidente', 'tipo_acidente']:
                    if c in colunas:
                        group_col = c
                        break
            elif 'situacao' in pergunta_baixa:
                for c in ['situacao']:
                    if c in colunas:
                        group_col = c
                        break

            sql_parts.append(f"SELECT {group_col}, COUNT(*) as total FROM {tname}")
        else:
            sql_parts.append(f"SELECT COUNT(*) as total FROM {tname}")
    else:
        # SELECT * limitado
        select_cols = colunas[:10]
        sql_parts.append(f"SELECT {', '.join(select_cols)} FROM {tname}")

    # WHERE
    where_parts = []

    # Detectar UF no WHERE
    if has_uf:
        for uf in ['sp', 'rj', 'mg', 'ba', 'rs', 'pr', 'sc', 'go', 'ce', 'pa', 'am', 'pe', 'rn', 'pb', 'al', 'df', 'ma', 'pi', 'se', 'mt', 'to', 'ac', 'ap', 'ro']:
            if uf in pergunta_baixa:
                uf_col = None
                for c in ['uf', 'sg_uf', 'nm_uf', 'cd_uf']:
                    if c in colunas:
                        uf_col = c
                        break
                if uf_col:
                    if uf_col.startswith('nm_'):
                        where_parts.append(f"{uf_col} LIKE '%{uf.upper()}%'")
                    else:
                        where_parts.append(f"{uf_col} = '{uf.upper()}'")

    # Detectar período
    if has_date:
        for ano in ['2024', '2023', '2022', '2021', '2020']:
            if ano in pergunta_baixa:
                if 'data_inversa' in colunas:
                    where_parts.append(f"data_inversa LIKE '{ano}%'")
                elif 'vl_br' in colunas and tname == 'contagem_trafego':
                    where_parts.append(f"1=1")

    if where_parts:
        sql_parts.append("WHERE " + " AND ".join(where_parts))

    # GROUP BY
    if has_group and has_count:
        parts = sql_parts[-1].split("FROM")
        if len(parts) == 2:
            sql_parts[-1] = parts[0].rstrip() + f" GROUP BY {group_col}" + " FROM" + parts[1]

    # ORDER BY
    if has_order or has_top:
        if has_count:
            parts = sql_parts[-1].split("FROM")
            if len(parts) == 2:
                sql_parts[-1] = parts[0].rstrip() + " ORDER BY total DESC" + " FROM" + parts[1]
        else:
            order_col = colunas[0] if colunas else '*'
            sql_parts[-1] = sql_parts[-1] + f" ORDER BY {order_col}"

    # LIMIT
    if has_top or has_limit:
        sql_parts.append(f"LIMIT {limit_val}")

    return "\n".join(sql_parts)


# ============================================================
# Execucao SQL
# ============================================================
def executar_sql(sql):
    """Executar SQL e retornar resultados."""
    import psycopg2

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        if cursor.description:
            rows = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            # Converter para dict para serialização JSON
            resultados = []
            for row in rows:
                resultados.append(dict(zip(colunas, row)))
            return colunas, resultados
        else:
            return [], []
    except Exception as e:
        return None, str(e)
    finally:
        cursor.close()
        conn.close()


# ============================================================
# Responder pergunta
# ============================================================
def responder_pergunta(pergunta, json_output=False):
    """Processar pergunta e retornar resultados."""
    start_time = time.time()

    # 1. Buscar no dicionário de dados (FAISS)
    dicionario_docs = []
    if check_faiss_index():
        dicionario_docs = search_dicionario(pergunta, top_k=2)

    # 2. Gerar SQL
    resultados_sql = gerar_sql(pergunta)

    # 3. Executar cada SQL
    resultados = []
    for tname, sql in resultados_sql:
        colunas, rows = executar_sql(sql)
        resultados.append({
            "tabela": tname,
            "sql": sql,
            "colunas": colunas,
            "num_linhas": len(rows) if rows else 0,
            "dados": rows,
            "erro": None if rows else True
        })

    elapsed = round(time.time() - start_time, 2)

    if json_output:
        return json.dumps({
            "pergunta": pergunta,
            "num_tabelas": len(resultados),
            "resultados": resultados,
            "tempo_s": elapsed,
            "dicionario_contexto": [
                {"chunk_id": d.metadata.get('chunk_id', i), "texto": d.page_content[:500]}
                for i, d in enumerate(dicionario_docs)
            ],
            "schema_tabelas": {
                nome: {
                    "descricao": info["descricao"],
                    "periodo": info["periodo"],
                    "colunas": info["colunas_desc"]
                }
                for nome, info in TABELAS_INFO.items()
            }
        }, ensure_ascii=False, indent=2)
    else:
        lines = [
            "=" * 60,
            "  Pergunte aos Dados - Dados Estruturados",
            f"  Pergunta: {pergunta}",
            f"  Tempo de processamento: {elapsed}s",
            "=" * 60,
        ]

        for r in resultados:
            lines.append(f"\n  Tabela: {r['tabela']}")
            lines.append(f"  SQL: {r['sql']}")
            lines.append(f"  Registros: {r['num_linhas']}")
            lines.append(f"  Colunas: {', '.join(r['colunas'])}")

            # Mostrar dados (limitado a 5 linhas para legibilidade)
            if r['dados'] and r['num_linhas'] > 0:
                for i, row in enumerate(r['dados'][:5]):
                    line_parts = []
                    for col in r['colunas']:
                        val = row.get(col, '')
                        if val is None:
                            val = '(NULL)'
                        line_parts.append(f"{col}={val}")
                    lines.append(f"    {i+1}. {', '.join(line_parts)}")
                if r['num_linhas'] > 5:
                    lines.append(f"    ... e mais {r['num_linhas'] - 5} registros")
            elif r.get('erro'):
                lines.append(f"  ERRO: {r['dados']}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# ============================================================
# Listar tabelas
# ============================================================
def listar_tabelas():
    """Listar todas as tabelas disponíveis."""
    print("=" * 60)
    print("  Tabelas disponíveis no banco de dados estruturado")
    print("=" * 60)
    for nome, info in TABELAS_INFO.items():
        print(f"\n  Tabela: {nome}")
        print(f"  Descrição: {info['descricao']}")
        print(f"  Período: {info['periodo']}")
        print(f"  Registros: {info['registros']:,}")
        print(f"  Colunas:")
        for col, desc in info['colunas_desc'].items():
            print(f"    - {col}: {desc}")
    print("\n" + "=" * 60)


# ============================================================
# Schema do banco
# ============================================================
def gerar_schema():
    """Gerar schema SQL das tabelas."""
    import psycopg2

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tabelas = cursor.fetchall()

        print("=" * 60)
        print("  Schema do banco de dados")
        print("=" * 60)
        print(f"\n  Tabelas encontradas ({len(tabelas)}):")
        for t in tabelas:
            print(f"    - {t[0]} ({t[1]})")

        # Para cada tabela, mostrar colunas
        for t in tabelas:
            tname = t[0]
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (tname,))
            colunas = cursor.fetchall()

            print(f"\n  Tabela: {tname}")
            print(f"  Colunas ({len(colunas)}):")
            for col in colunas:
                null_str = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"    - {col[0]} ({col[1]}) [{null_str}]")

        print("\n" + "=" * 60)

    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        cursor.close()
        conn.close()


# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Pergunte aos Dados - Consultar bases de dados estruturadas via SQL",
        epilog="Exemplo: structured-query.py 'Quantos acidentes houve em SP em 2024?'"
    )
    parser.add_argument(
        "question", nargs="?", default=None,
        help="Pergunta sobre os dados estruturados"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Saida em formato JSON"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Verificar se o sistema esta configurado"
    )
    parser.add_argument(
        "--schema", action="store_true",
        help="Mostrar schema do banco de dados"
    )
    parser.add_argument(
        "--list-tables", action="store_true",
        help="Listar todas as tabelas e colunas"
    )
    parser.add_argument(
        "--build-index", action="store_true",
        help="(Re)construir o indice FAISS"
    )
    parser.add_argument(
        "--top-k", type=int, default=2,
        help="Numero de chunks do dicionario a recuperar (padrao: 2)"
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

    # Schema
    if args.schema:
        gerar_schema()
        sys.exit(0)

    # Listar tabelas
    if args.list_tables:
        listar_tabelas()
        sys.exit(0)

    # Requer pergunta
    if not args.question:
        parser.print_help()
        sys.exit(1)

    # Verificar PostgreSQL
    if not verificar_postgres():
        print("ERRO: PostgreSQL não acessível. Verifique a configuração.", file=sys.stderr)
        sys.exit(1)

    try:
        result = responder_pergunta(
            pergunta=args.question,
            json_output=args.json_output
        )
        print(result)
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
