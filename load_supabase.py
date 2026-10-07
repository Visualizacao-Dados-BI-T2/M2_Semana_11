# importando as bibliotecas
import os
import toml
import pandas as pd
from sqlalchemy import create_engine

SECRETS_PATH = os.path.join(".streamlit", "secrets.toml") # joinando caminho da pasta de secrets.
CSV_PATH = "dados_b3_reais.csv" # nome do arquivo a ser enviado

def carregar_dados_no_supabase():
    if not os.path.exists(SECRETS_PATH):
        print(f"[ERRO] Arquivo de segredos '{SECRETS_PATH}' não encontrado.")
        return

    secrets = toml.load(SECRETS_PATH)
    db_config = secrets.get("connections", {}).get("postgresql", {})

    if not db_config:
        print("[ERRO] Seção [connections.postgresql] não encontrada em secrets.toml.")
        return

    # Suporta chaves minúsculas (padrão do Streamlit) e maiúsculas
    if "url" in db_config:
        connection_url = db_config["url"]
    else:
        user = db_config.get("username")
        pwd = db_config.get("password")
        host = db_config.get("host")
        port = db_config.get("port")
        dbname = db_config.get("database")
        
        # Conexão com driver psycopg2
        connection_url = f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{dbname}"

    host_display = db_config.get("host")
    print(f"-> Conectando ao Supabase em: {host_display} (Porta: {port})...")
    engine = create_engine(connection_url)

    print(f"-> Lendo arquivo local: {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    df["data"] = pd.to_datetime(df["data"]).dt.date

    print(f"-> Inserindo {len(df)} registros na tabela 'acoes_b3' no Supabase...")
    df.to_sql("acoes_b3", engine, if_exists="replace", index=False)
    print("Sucesso! Dados carregados na nuvem com sucesso no Supabase.")

if __name__ == "__main__":
    carregar_dados_no_supabase()
