# importar bibliotecas
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, date, timedelta
import sqlalchemy

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


# --------------------------------------------------------------------------
# PRÁTICA GUIADA DA AULA 1: CONSULTA SQL PARAMETRIZADA (Slide 15)
# --------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "### 🔬 Prática Guiada da Aula 1: Consulta SQL Parametrizada (`params`)"
)
st.info(
    "**Objetivo do Slide 15:** Construir uma consulta onde o usuário seleciona um parâmetro na tela "
    "e a query SQL é executada trazendo apenas o recorte filtrado usando parâmetros seguros (`:param`), "
    "prevenindo ataques de SQL Injection."
)

# Passo 1: Organização visual em 2 colunas
# Coluna 1 (esquerda, proporção 1): Controles interativos (inputs do usuário)
# Coluna 2 (direita, proporção 2): Código SQL/Python gerado dinamicamente para os alunos verem
col_p1, col_p2 = st.columns([1, 2])

with col_p1:
    # Widget 1: Selectbox para o aluno escolher o ativo (ticker)
    # key única garante que o widget não colida com os filtros da barra lateral
    ticker_param = st.selectbox(
        "Selecione um Ativo para a Query:",
        options=todos_tickers,
        index=0,
        key="param_ticker_aula1",
        help="Este valor será injetado com segurança no parâmetro :ticker do SQL."
    )
    
    # Widget 2: Slider numérico para limitar a quantidade de registros retornados (LIMIT)
    limite_linhas = st.slider(
        "Qtd. Registros (LIMIT):", 
        min_value=5, 
        max_value=30, 
        value=10, 
        step=5,
        help="Define o teto de linhas na cláusula LIMIT :limite da query."
    )
    
    # Widget 3: Botão de ação explícita
    # O botão impede que uma query pesada seja disparada antes do usuário terminar de escolher
    executar_query = st.button(
        "🚀 Executar Query SQL Parametrizada", 
        use_container_width=True
    )

with col_p2:
    # Exibição pedagógica do código Python exato que roda nos bastidores
    # Notem os marcadores :ticker e :limite -> eles NUNCA usam concatenação de strings com f-string!
    sql_exemplo = f"""# 1. Abre o conector nativo do Streamlit gerenciando a conexão
                    conn = st.connection("postgresql", type="sql")

                    # 2. Define a query com parâmetros de substituição seguros (:ticker e :limite)
                    #    IMPORTANTE: Nunca use f-strings com SQL direto (ex: "WHERE ticker = '{ticker_param}'")
                    #    Concatenação direta abre vulnerabilidade para ataques de SQL Injection!
                    query = \"\"\"
                        SELECT data, preco_fechamento, volume, ticker 
                        FROM acoes_b3 
                        WHERE ticker = :ticker 
                        ORDER BY data DESC 
                        LIMIT :limite;
                    \"\"\"

                    # 3. Executa a query passando os valores mapeados no dicionário 'params'
                    #    O conector sanitiza e trata os tipos (string, int) automaticamente:
                    df = conn.query(
                        query, 
                        params={{"ticker": "{ticker_param}", "limite": {limite_linhas}}},
                        ttl=0  # ttl=0 garante que a consulta ao vivo não use cache antigo no teste
                    )"""
    st.code(sql_exemplo, language="python")

# Passo 2: Execução condicional disparada apenas quando o botão for clicado
if executar_query:
    # st.spinner exibe um feedback visual de carregamento enquanto o banco processa
    with st.spinner("Executando query SQL parametrizada no banco..."):
        try:
            # Obtém a conexão ativa do Streamlit
            conn = st.connection("postgresql", type="sql")
            
            # Se estamos conectados ao vivo no Supabase, roda a query diretamente no banco na nuvem
            if conn is not None and "Supabase" in origem_dados:
                query_sql = (
                    "SELECT data, preco_fechamento, volume, ticker "
                    "FROM acoes_b3 "
                    "WHERE ticker = :ticker "
                    "ORDER BY data DESC "
                    "LIMIT :limite;"
                )
                
                # conn.query() executa com os parâmetros fornecidos e retorna um DataFrame do Pandas
                df_resultado_param = conn.query(
                    query_sql,
                    params={"ticker": ticker_param, "limite": limite_linhas},
                    ttl=0,  # ttl=0 força a consulta em tempo real sem reaproveitar cache
                )
                st.success(
                    f"Query SQL executada com sucesso no Supabase! Retornados {len(df_resultado_param)} registros."
                )
            else:
                # Mecanismo de Fallback Pedagógico:
                # Se o banco remoto estiver inacessível, simula a mesma query filtrando o CSV em memória
                df_resultado_param = (
                    df_bruto[df_bruto["ticker"] == ticker_param]
                    .sort_values(by="data", ascending=False)
                    .head(limite_linhas)
                )
                st.info(
                    f"Executado em modo Fallback Local para o ticker **{ticker_param}** ({len(df_resultado_param)} registros)."
                )

            # Passo 3: Apresentação tabular dos dados retornados
            # Usamos column_config para formatar datas e moedas no padrão visual corporativo
            st.dataframe(
                df_resultado_param,
                column_config={
                    "data": st.column_config.DateColumn(
                        "Data", format="DD/MM/YYYY"
                    ),
                    "preco_fechamento": st.column_config.NumberColumn(
                        "Preço Fechamento", format="R$ %.2f"
                    ),
                    "volume": st.column_config.NumberColumn("Volume", format="%d"),
                    "ticker": st.column_config.TextColumn("Ticker"),
                },
                use_container_width=True,
                hide_index=True,
            )
        except Exception as erro_exec:
            # Tratamento de exceção amigável: mostra o erro sem quebrar a aplicação do aluno
            st.error(f"Erro ao executar query parametrizada: {erro_exec}")
