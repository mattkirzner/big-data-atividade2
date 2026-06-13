from prefect import flow, task, get_run_logger
from extract import Extract
from transform import Transform
from connectToAtlas import ConnectToAtlas as Atlas
from spark_pncp import PNCPSparkPipeline as Spark
import os


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL = os.getenv("DB_URL")


extract_settings = {
    "data_inicial": "20250101",
    "data_final": "20251231",
    "codigo_modalidade_contratacao": 6,
    "pagina": 1,
    "tamanhoPagina": None,
    "codigo_modo_disputa": None,
    "uf": "PE",
    "codigo_municipio_ibge": None,
}


atlas_settings = {
    "user": DB_USER,
    "password": DB_PASSWORD,
    "atlas_url": DB_URL,
    "cluster_name": "PNCP",
    "collection_name": "aula_teste",
}


sqlite_settings = {
    "db_path": os.getenv("SQLITE_DB_PATH", "/app/PNCP_LOCAL.db"),
    "table_name": os.getenv("SQLITE_TABLE_NAME", "contratacoes_pncp"),
}


atlas = Atlas(atlas_settings["user"], atlas_settings["password"], atlas_settings["atlas_url"])


@task(retries=3, retry_delay_seconds=10)
def extract_task(settings: dict) -> list[dict]:
    """Extrai os dados brutos diretamente da API do PNCP."""
    logger = get_run_logger()
    extract = Extract()
    logger.info("Iniciando extração via API do PNCP...")
    data = extract.extract_contratacoes_pncp(
        settings["data_inicial"],
        settings["data_final"],
        settings["codigo_modalidade_contratacao"],
        settings["pagina"],
        settings["tamanhoPagina"],
        settings["codigo_modo_disputa"],
        settings["uf"],
        settings["codigo_municipio_ibge"],
    )
    logger.info(f"Registros extraídos da API: {len(data.get('data', []))}")
    return data


@task
def transform_task(data: list) -> list:
    """Aplica as regras de negócio iniciais e filtragens nos dados da API."""
    logger = get_run_logger()
    if not data:
        logger.warning("Nenhum dado recebido para transformar.")
        return []
    transform = Transform()
    logger.info("Iniciando transformação de negócio...")
    clean_data = transform.filtrar_dados_pncp(data)
    logger.info("Transformação de negócio concluída.")
    return clean_data


@task
def upload_atlas_task(settings: dict, data: list):
    """Envia os dados validados de negócio para a camada de Landing/Raw no Atlas."""
    logger = get_run_logger()
    logger.info(f"Conectando ao AtlasDB e iniciando upload na coleção '{settings['collection_name']}'...")
    result = atlas.upload_pncp_data(
        settings["cluster_name"], settings["collection_name"], data
    )
    logger.info(f"Sucesso: {len(result)} registros inseridos na nuvem.")


@task
def download_atlas_task(settings: dict) -> list[dict]:
    """
    BAIXA todos os dados contidos na coleção do Atlas de forma isolada,
    garantindo que o Spark não possua acoplamento com o banco de origem.
    """
    logger = get_run_logger()
    logger.info(f"Baixando dados brutos da nuvem (Coleção: '{settings['collection_name']}') para processamento...")
    
    # Executa a leitura nativa do dicionário de documentos do Atlas
    dados_brutos = atlas.read_data(
        db_name=settings["cluster_name"], 
        collection_name=settings["collection_name"]
    )
    
    logger.info(f"Download concluído: {len(dados_brutos)} documentos recuperados.")
    return dados_brutos
    

@task 
def save_with_spark_task(data: list, sqlite_db_path: str, sqlite_table_name: str, collection_name: str):
    """
    PROCESSA E SALVA os dados localmente utilizando o motor do PySpark.
    A classe Spark recebe apenas a lista pura de dados, mantendo o baixo acoplamento.
    """
    logger = get_run_logger()
    if not data:
        logger.warning("Nenhum dado disponível para o Spark processar.")
        return

    logger.info("Iniciando o motor local do Spark para limpeza técnica e validação de Schema...")
    
    pipeline = Spark()
    
    try:
        dados_tratados = pipeline.clean_raw_data(data)
        
        df_pandas = pipeline.process_with_spark(dados_tratados, collection_name)

        logger.info(f"Gravando de forma incremental no SQLite local ({sqlite_db_path})...")
        pipeline.load_to_sqlite(df_pandas, sqlite_db_path, sqlite_table_name)
        
    except Exception as e:
        logger.error(f"Falha crítica no pipeline do Spark: {str(e)}")
        raise e
    finally:

        pipeline.stop()


@flow(name="ETL PNCP Atlas Prefect", log_prints=True)
def etl_atlas_flow():
    """Fluxo principal do Prefect orquestrando todo o pipeline de dados."""
    logger = get_run_logger()
    
    data_raw = extract_task(extract_settings)
    clean_data = transform_task(data_raw)
    
    if clean_data:
        upload_atlas_task(atlas_settings, clean_data)
    else:
        logger.warning("Fluxo interrompido na Etapa 1: Sem dados para upload.")
        return


    dados_para_processar = download_atlas_task(atlas_settings)
    
    save_with_spark_task(
        data=dados_para_processar,
        sqlite_db_path=sqlite_settings["db_path"],
        sqlite_table_name=sqlite_settings["table_name"],
        collection_name=atlas_settings["collection_name"]
    )
    
    logger.info("🏁 Fluxo completo executado com sucesso e dados prontos para o Chatbot!")


if __name__ == "__main__":
    etl_atlas_flow()