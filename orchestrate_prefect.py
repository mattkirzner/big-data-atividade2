from prefect import flow, task, get_run_logger
from src import Extract
from src import ConnectToAtlas as Atlas
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import os


load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL = os.getenv("DB_URL")

extract_settings = {
    "data_inicial":"20250101",
    "data_final":"20251231",
    "codigo_modalidade_contratacao":6,
    "pagina":2,
    "tamanhoPagina":50,
    "codigo_modo_disputa":None,
    "uf":"PE",
    "codigo_municipio_ibge":None
}
upload_settings={
    "user": DB_USER,
    "password": DB_PASSWORD,
    "atlas_url": DB_URL,
    "cluster_name": "PNCP",
    "collection_name": "prefect_teste"
}

def create_spark_session(app_name: str = "ETL_PNCP_Spark") -> SparkSession:
    return SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .getOrCreate()

@task(retries=3, retry_delay_seconds=10)
def extract_task(settings: dict) -> list[dict]:
    logger = get_run_logger()
    extract = Extract()
    logger.info("Iniciando extração")
    data = extract.extract_contratacoes_pncp(settings["data_inicial"],
        settings["data_final"],
        settings["codigo_modalidade_contratacao"],
        settings["pagina"],
        settings["tamanhoPagina"],
        settings["codigo_modo_disputa"],
        settings["uf"],
        settings["codigo_municipio_ibge"])
    logger.info(f"Registros extraidos: {len(data['data'])}")
    return data
    
@task
def transform_task(data: dict) -> list[dict]:
    logger = get_run_logger()
    if not data or not data.get("data"):
        logger.warning("Nenhum dado disponível para transformar.")
        return []

    rows = data["data"]
    logger.info(f"Transformando {len(rows)} registros com Spark")
    spark = create_spark_session("ETL_PNCP_Transform")
    try:
        df = spark.createDataFrame(rows)
        df_clean = df.select(
            col("numeroControlePNCP").alias("id"),
            col("orgaoEntidade.razaoSocial").alias("entidade"),
            col("unidadeOrgao.municipioNome").alias("municipio"),
            col("unidadeOrgao.ufSigla").alias("uf"),
            col("objetoCompra").alias("descricao"),
            col("valorTotalEstimado").cast("double").alias("valor"),
            col("modalidadeNome").alias("modalidade"),
            col("situacaoCompraNome").alias("status"),
            col("linkSistemaOrigem").alias("linkOrigem"),
            col("dataPublicacaoPncp").substr(1, 10).alias("data_publicacao")
        )

        clean_data = [row.asDict(recursive=True) for row in df_clean.collect()]
        logger.info(f"Registros transformados: {len(clean_data)}")
        return clean_data
    finally:
        spark.stop()

@task
def upload_atlas_task(settings: dict, data):
    logger = get_run_logger()
    logger.info("Iniciando conexão ao AtlasDB")
    atlas = Atlas(settings["user"], settings["password"], settings["atlas_url"])
    logger.info("Iniciando upload")
    result = atlas.upload_pncp_data(settings["cluster_name"], settings["collection_name"], data)
    logger.info(f"{len(result)} registros inseridos em {settings["collection_name"]}")
                
@flow(name="ETL PNCP Atlas Prefect", log_prints=True)
def etl_atlas_flow():
    logger = get_run_logger()
    data = extract_task(extract_settings)
    clean_data = transform_task(data)
    if clean_data:
        upload_atlas_task(upload_settings, clean_data)
        logger.info("Fluxo concluído: dados enviados ao Atlas.")
    else:
        logger.info("Fluxo encerrado: Sem dados para upload.")

if __name__ == "__main__":
    etl_atlas_flow()

