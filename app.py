# importar bibliotecas
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, date, timedelta

# configuracao de segurança de exibição da pagina
pd.set_option("styler.render.max_elements", 1_000_000) # define o numero máximo de elementos a serem exibidos na pagina.

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA & IDENTIDADE VISUAL
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Financeiro B3 | Análise Avançada", # Titulo da pagina
    page_icon="📈", # Icone da pagina
    layout="wide", # Layout da pagina
    initial_sidebar_state="expanded", # Estado inicial da barra lateral
)

DIRETORIO_RAIZ = os.path.dirname(os.path.abspath(__file__)) # caminho da raiz do projeto
CAMINHO_CSV = os.path.join(DIRETORIO_RAIZ, "dados_b3_reais.csv") # fallback de dados (2°  opção caso a primeira falhe)

# Estilização CSS refinada (Dark Mode Premium)
st.markdown(
    """
        <style>
            /* Estilização dos cartões de métrica */
            div[data-testid="stMetric"] {
                background-color: #1A1F2C;
                border: 1px solid #2D3748;
                border-radius: 10px;
                padding: 16px 20px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
            }
            div[data-testid="stMetricLabel"] {
                color: #9CA3AF !important;
                font-weight: 500;
                font-size: 0.9rem;
            }
            div[data-testid="stMetricValue"] {
                color: #F3F4F6 !important;
                font-weight: 700;
                font-size: 1.6rem;
            }
            .badge-cloud {
                background-color: #064E3B;
                color: #34D399;
                border: 1px solid #059669;
                padding: 5px 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.85rem;
                display: inline-block;
            }
            .badge-fallback {
                background-color: #78350F;
                color: #FCD34D;
                border: 1px solid #D97706;
                padding: 5px 12px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.85rem;
                display: inline-block;
            }
        </style>
    """,
        unsafe_allow_html=True,
)

# ==============================================================================
# 🔒 [AULA 01] CONEXÃO COM BANCO DE DADOS, SEGURANÇA (SECRETS) E FALLBACK
# ==============================================================================

@st.cache_data() # salvar dados em cache para incremento de performance na aplicação
def _consultar_supabase():
    """
    Executa a query diretamente no Supabase.
    Se a conexão for bem-sucedida, o resultado é cacheado por 10 minutos.
    Se houver erro, a exceção é disparada e o Streamlit NÃO armazena o erro em cache!
    """

    conn = st.connection("postgresql", type="sql") # instanciamento de conexão
    query = (
        "SELECT data, preco_fechamento, volume, ticker FROM acoes_b3 ORDER BY data ASC;"
    )
    df = conn.query(query)

    if df is None or df.empty:
        raise ValueError("A consulta ao banco Supabase retornou vazia!")

    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["preco_fechamento"] = pd.to_numeric(df["preco_fechamento"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df = (
        df.dropna(subset=["preco_fechamento", "data"])
        .sort_values(by=["ticker", "data"])
        .reset_index(drop=True)
    )

    return df

def carregar_dados():
    """
    Coordena a carga com resiliência: tenta o Supabase e, em caso de falha,
    aciona imediatamente o Fallback local sem contaminar a memória de cache.
    """
    try: # tentando conectar ao supabase
        df = _consultar_supabase()
        return df, "Supabase (PostgreSQL Cloud)", None
    except Exception as erro:
        df_local = pd.read_csv(CAMINHO_CSV)
        df_local["data"] = pd.to_datetime(df_local["data"]).dt.date
        df_local["preco_fechamento"] = pd.to_numeric(df_local["preco_fechamento"], errors="coerce")
        df_local["volume"] = pd.to_numeric(df_local["volume"], errors="coerce")
        df_local = (
            df_local.dropna(subset=["preco_fechamento", "data"])
            .sort_values(by=["ticker", "data"])
            .reset_index(drop=True)
        )
        return df_local, "Fallback Local (dados_b3_reais.csv)", str(erro)


# Carga dos dados (resiliente e com cache ativo)
df_bruto, origem_dados, erro_conexao = carregar_dados()


# Metadados e variáveis de controle inicial
todos_tickers = sorted(df_bruto["ticker"].unique().tolist())
data_minima = df_bruto["data"].min()
data_maxima = df_bruto["data"].max()

# Seleção inicial inteligente: 4 blue chips conhecidas para evitar sobrecarga visual
tickers_padrao_sugeridos = [
    t for t in ["PETR4", "VALE3", "ITUB4", "WEGE3"] if t in todos_tickers
]
if not tickers_padrao_sugeridos:
    tickers_padrao_sugeridos = todos_tickers[:4]

# Data inicial padrão: últimos 3 anos para foco no cenário recente de mercado
data_inicio_padrao = max(data_minima, data_maxima - timedelta(days=365 * 3))
