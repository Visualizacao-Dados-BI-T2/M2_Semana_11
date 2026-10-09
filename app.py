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
# Conceitos da Aula 1:
# 1. Conexão com banco relacional na nuvem (PostgreSQL / Supabase) via st.connection
# 2. Segurança de credenciais: .streamlit/secrets.toml protegido pelo .gitignore
# 3. Resiliência de dados: fallback automático para CSV local caso a rede falhe
# ==============================================================================

@st.cache_data(ttl=600, show_spinner="Consultando dados de mercado no Supabase...") # salvar dados em cache para incremento de performance na aplicação
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
    df = conn.query(query, ttl=600) # gravando a conexão em uma variavel

    if df is None or df.empty: # validando se a conexão foi bem sucedida e retornou dados
        raise ValueError("A consulta ao banco Supabase retornou vazia!")


    # Padronização e limpeza dos dados
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
        return df, "Supabase (PostgreSQL Cloud)", None # retornando os dados, a origem e o erro (none)
    except Exception as erro: # caso ocorra erro
        df_local = pd.read_csv(CAMINHO_CSV) # carregando os dados locais

        # Padronização e limpeza dos dados
        df_local["data"] = pd.to_datetime(df_local["data"]).dt.date
        df_local["preco_fechamento"] = pd.to_numeric(df_local["preco_fechamento"], errors="coerce")
        df_local["volume"] = pd.to_numeric(df_local["volume"], errors="coerce")
        df_local = (
            df_local.dropna(subset=["preco_fechamento", "data"])
            .sort_values(by=["ticker", "data"])
            .reset_index(drop=True)
        )
        return df_local, "Fallback Local (dados_b3_reais.csv)", str(erro) # retornando os dados, a origem e o erro


# Carga dos dados (resiliente e com cache ativo)
df_bruto, origem_dados, erro_conexao = carregar_dados()


# Metadados e variáveis de controle inicial - Definição do filtros pré carregados.
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


# ==============================================================================
# ⚡ [AULA 02] PERFORMANCE (CACHE), ESTADO (SESSION_STATE) & FILTROS CRUZADOS
# ==============================================================================
# Conceitos da Aula 2:
# 1. Comparativo @st.cache_data (dados e tabelas) vs @st.cache_resource (conexões)
# 2. Gerenciamento de estado (st.session_state) para manter filtros e callback de reset
# 3. Construção de filtros reativos cruzados na barra lateral (st.sidebar)
# ==============================================================================

@st.cache_resource # cache de recursos
def obter_conexao_persistente(): # conexão com o banco de dados
    """
    Demonstração prática de @st.cache_resource:
    Retorna a instância compartilhada do gerenciador de conexão sem recriá-la na memória.
    """
    try: 
        return st.connection("postgresql", type="sql") # conectando ao banco de dados
    except Exception:
        return None


# Inicialização segura do estado da sessão (Session State)
if "filtro_tickers" not in st.session_state: # validando se a chave 'filtro_tickers' existe no estado da sessão
    st.session_state.filtro_tickers = tickers_padrao_sugeridos

if "filtro_periodo" not in st.session_state: # validando se a chave 'filtro_periodo' existe no estado da sessão
    st.session_state.filtro_periodo = (data_inicio_padrao, data_maxima)


def resetar_filtros():
    """Callback disparado pelo botão para restaurar os filtros ao estado padrão limpo"""
    st.session_state.filtro_tickers = tickers_padrao_sugeridos
    st.session_state.filtro_periodo = (data_inicio_padrao, data_maxima)



# ------------------------------------------------------------------------------
# BARRA LATERAL: FILTROS REATIVOS CRUZADOS (st.sidebar)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Filtros do Mercado")

    # Status da conexão
    if "Supabase" in origem_dados:  # validando conexão supabase ou local
        st.markdown(
            f'<span class="badge-cloud">🟢 {origem_dados}</span>',  # badge de conexão supabase com sucesso
            unsafe_allow_html=True,  # fazendo o markdown entender o HTML acima
        )
        st.caption(
            "Conectado ao vivo com o banco PostgreSQL no Supabase."
        )  # feedback de conexão
    else:
        st.markdown(
            f'<span class="badge-fallback">🟡 {origem_dados}</span>',
            unsafe_allow_html=True,
        )
        if erro_conexao:
            with st.expander("🔍 Motivo do Fallback (Diagnóstico):", expanded=True):
                st.caption("Erro retornado ao tentar conectar no Supabase:")
                st.code(erro_conexao, language="bash")
        st.caption("Configure as credenciais no secrets.toml ou no painel da nuvem.")

    st.markdown("---")

    # Filtro 1: Seleção de Ativos
    tickers_selecionados = st.multiselect(
        "Selecione os Ativos (Tickers):",
        options=todos_tickers,
        key="filtro_tickers", # define uma chave de validação unica para o objeto
        help="Dica: selecione de 1 a 5 ativos para uma visualização gráfica mais limpa.",
    )


    # Filtro 2: Período de Análise
    periodo_selecionado = st.date_input(
        "Período de Análise:",
        min_value=data_minima,
        max_value=data_maxima,
        key="filtro_periodo",
        help="Selecione a data de início e fim.",
    )

    # # Filtro 2: Período de Análise
    # periodo_selecionado_inicial = st.date_input(
    #     "Período de Análise:",
    #     value=data_minima,
    #     key="filtro_periodo",
    #     help="Selecione a data de início e fim.",
    # )

    # periodo_selecionado_final = st.date_input(
    #     "Período de Análise:",
    #     value=data_maxima,
    #     key="filtro_periodo",
    #     help="Selecione a data de início e fim.",
    # )


    st.markdown("### 🎛️ Visualização do Gráfico")

    # Filtro 3: Normalização Base 100
    modo_comparativo = st.toggle(
        "Comparar Retorno (Base 100)",
        value=False,
        help="Converte a cotação inicial de cada ação para 100 e compara a rentabilidade acumulada percentual.",
    )

    # Filtro 4: Escala Logarítmica
    escala_log = st.toggle(
        "Escala Logarítmica (Eixo Y)",
        value=False,
        help="Útil para visualizar ações com preços muito diferentes (ex: R$ 5 vs R$ 10.000) sem distorcer o gráfico.",
    )

    st.markdown("---")
    st.button(
        "🔄 Restaurar Padrão Limpo", on_click=resetar_filtros, use_container_width=True
    ) # botão para resetar os filtros

    st.markdown("---")
    st.caption("FIESC / SENAI • Visualização de Dados e BI\nM2S11 - Streamlit Avançado")

# ==============================================================================
# APLICAÇÃO DOS FILTROS CRUZADOS NO DATAFRAME
# ==============================================================================
if not tickers_selecionados:
    st.warning(
        "⚠️ Selecione pelo menos um ticker na barra lateral para visualizar o dashboard."
    )
    st.stop()

# Validação do intervalo de datas
if isinstance(periodo_selecionado, (tuple, list)) and len(periodo_selecionado) == 2: # validando se o periodo selecionado é uma tupla ou lista com 2 elementos
    d_inicio, d_fim = periodo_selecionado # definindo o periodo inicial e final
elif isinstance(periodo_selecionado, (tuple, list)) and len(periodo_selecionado) == 1: # validando se o periodo selecionado é uma tupla ou lista com 1 elemento
    d_inicio = periodo_selecionado[0]
    d_fim = data_maxima
else: # caso contrario
    d_inicio, d_fim = data_inicio_padrao, data_maxima # define o periodo inicial e final

# ==============================================================================
# APLICAÇÃO DOS FILTROS CRUZADOS NO DATAFRAME
# ==============================================================================

# Filtragem encadeada
df_filtrado = df_bruto[
    (df_bruto["ticker"].isin(tickers_selecionados)) # filtrando pelo ticker
    & (df_bruto["data"] >= d_inicio) # filtrando pela data de inicio
    & (df_bruto["data"] <= d_fim) # filtrando pela data de fim
].copy() # copia do dataframe filtrado

if df_filtrado.empty: # validando se o dataframe filtrado está vazio
    st.info(
        "Nenhum dado encontrado para o período ou ticker selecionado. Tente expandir o intervalo de datas ou mudar o ticker selecionado."
    )
    st.stop()
