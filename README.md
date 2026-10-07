# 📈 Dashboard Financeiro B3 | Streamlit Avançado

Projeto prático desenvolvido para o módulo de **Visualização de Dados & Business Intelligence (Módulo 2 / Semana 11)**.  
A aplicação explora conceitos avançados de arquitetura de dados e interface com **Streamlit**, conectando-se a um banco de dados em nuvem (**Supabase / PostgreSQL**) com arquitetura de alta resiliência e consultas SQL parametrizadas.

---

## 🎯 Destaques e Boas Práticas Implementadas

- **Conexão Nativa com Banco de Dados:** Utilização de `st.connection("postgresql", type="sql")` via SQLAlchemy e driver PostgreSQL.
- **Resiliência e Fallback Local:** Sistema automático de tolerância a falhas que recorre ao arquivo `dados_b3_reais.csv` caso o banco remoto fique indisponível.
- **Cache Inteligente:** Uso otimizado de `@st.cache_data` para acelerar consultas e prevenir cacheamento de estados de erro.
- **Prevenção a SQL Injection:** Execução de consultas SQL parametrizadas seguras utilizando a cláusula `params={"ticker": ..., "limite": ...}`.
- **Visualização de Dados Interativa:** Renderização com componentes corporativos do Streamlit (`st.dataframe` com `column_config` customizado para moedas e datas) e gráficos dinâmicos com **Plotly**.

---

## 📂 Estrutura do Repositório

```text
├── .streamlit/
│   ├── secrets.toml.example  # Modelo de credenciais para conexão ao banco
│   └── secrets.toml          # Credenciais ativas (ignorado pelo Git via .gitignore)
├── app.py                    # Aplicação principal do Dashboard Financeiro
├── pratica_aula01.py         # Código e prática guiada de consultas SQL parametrizadas
├── load_supabase.py          # Script de ingestão/carga inicial do CSV no banco Supabase
├── dados_b3_reais.csv        # Dataset local contendo histórico de ativos da B3
├── requirements.txt          # Dependências do projeto
├── .gitignore                # Regras de exclusão do controle de versão
└── README.md                 # Documentação do projeto
```

---

## 🛠️ Tecnologias Utilizadas

- [Python 3.10+](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Pandas](https://pandas.pydata.org/)
- [Plotly](https://plotly.com/python/)
- [SQLAlchemy 2.0+](https://www.sqlalchemy.org/)
- [Psycopg (PostgreSQL Driver)](https://www.psycopg.org/)
- [Supabase (PostgreSQL Cloud)](https://supabase.com/)

---

## 🚀 Como Executar o Projeto

### 1. Clonar o Repositório

```bash
git clone git@github.com:Visualizacao-Dados-BI-T2/M2_Semana_11.git
cd M2_Semana_11
```

### 2. Criar e Ativar o Ambiente Virtual

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as Credenciais do Banco (`secrets.toml`)

Crie uma cópia do arquivo de exemplo dentro da pasta `.streamlit/`:

```bash
# Windows (cmd/PowerShell)
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Abra o arquivo `.streamlit/secrets.toml` e informe os dados de conexão do seu projeto Supabase:

```toml
[connections.postgresql]
dialect = "postgresql"
host = "aws-0-sa-east-1.pooler.supabase.com"
port = 6543
database = "postgres"
username = "postgres.seu_id_do_projeto"
password = "sua_senha_segura"
```

> ⚠️ **Atenção:** Nunca versione nem compartilhe o seu arquivo `.streamlit/secrets.toml`. Ele já está listado no `.gitignore`.

### 5. Carga de Dados Inicial no Supabase (Opcional)

Se a tabela `acoes_b3` ainda não estiver populada no Supabase, execute o script de migração:

```bash
python load_supabase.py
```

### 6. Executar a Aplicação Streamlit

Para iniciar o dashboard ou a prática guiada da aula:

```bash
# Para a prática guiada da aula:
streamlit run pratica_aula01.py

# Ou para a aplicação principal:
streamlit run app.py
```

A aplicação abrirá automaticamente no seu navegador em `http://localhost:8501`.
