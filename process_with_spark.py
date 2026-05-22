import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode # Útil se houver listas aninhadas
from prefect import task, get_run_logger

# 1. Carregar variáveis de ambiente
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL = os.getenv("DB_URL")  # Ex: cluster0.xxxx.mongodb.net

DB_NAME = "PNCP"
COL_NAME = "prefect_teste" # Ou "contratacoesLimpo"

# 2. Construir a URI de conexão do MongoDB Atlas para o Spark
# O formato padrão do Atlas usa mongodb+srv://
mongo_uri = f"mongodb+srv://{DB_USER}:{DB_PASSWORD}@{DB_URL}/{DB_NAME}.{COL_NAME}?retryWrites=true&w=majority"

# 3. Inicializar a SparkSession com o MongoDB Spark Connector
# Nota: A versão do pacote (4.1.1 neste exemplo) deve ser compatível com a sua versão do Spark
spark = SparkSession.builder \
    .appName("ETL_PNCP_Spark") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:4.1.1") \
    .config("spark.mongodb.read.connection.uri", mongo_uri) \
    .config("spark.mongodb.write.connection.uri", mongo_uri) \
    .getOrCreate()

@task
def executar_processamento_spark():
    logger = get_run_logger()
    spark = SparkSession.builder \
        .appName("Spark_Task_Prefect") \
        .master("local[*]") \
        .getOrCreate()
    try:
        logger.info("SparkSession iniciada.")
        df = spark.read.json("dados_contratacoes.json")
        df.show()
    except Exception as e:
        logger.error(f"Ocorreu um erro no Spark: {e}")
        raise
    finally:
        spark.stop()

def main():
    print(f"--- Lendo dados de {DB_NAME}.{COL_NAME} no MongoDB Atlas ---")
    
    # 4. Ler os dados do MongoDB para um DataFrame do Spark
    # O Spark lerá o BSON/JSON e inferirá o schema automaticamente
    df_raw = spark.read.format("mongodb").load()
    
    # Exibe o schema inferido para você entender a estrutura do JSON
    print("Schema Original:")
    df_raw.printSchema()
    
    # 5. Processamento e Estruturação Tabular
    # Dependendo de como a sua classe 'Transform' limpou os dados, eles podem estar dentro de um objeto ou array.
    # Vamos assumir que os dados limpos possuem campos como 'id', 'data', 'valor', ou uma chave principal 'data'.
    
    print("Amostra dos dados brutos do MongoDB:")
    df_raw.show(5, truncate=False)

    # EXEMPLO DE TRANSFORMAÇÃO (Ajuste conforme os campos reais do seu JSON do PNCP):
    # Se a API do PNCP retornou uma estrutura onde os dados úteis estão dentro de uma lista chamada 'data':
    # df_exploded = df_raw.select(explode(col("data")).alias("contratacao"))
    # df_tabular = df_exploded.select("contratacao.*")
    
    # Se os dados já foram salvos como documentos planos (flat) por linha na sua coleção:
    df_tabular = df_raw.select(
        col("_id").cast("string").alias("id_mongodb"), # Remove o tipo ObjectId do Mongo
        col("numeroCompra"), 
        col("anoCompra"),
        col("orgaoEntidade.razaoSocial").alias("orgao_razao_social"), # Acessando objetos aninhados
        col("valorTotalEstimado").cast("double").alias("valor_estimado"),
        col("objetoCompra")
    )

    print("--- Dados Estruturados em Formato Tabular ---")
    df_tabular.show(10, truncate=False)
    
    # 6. Próximas etapas: Armazenamento ou Visualização
    # Exemplo: Salvar em formato Parquet (altamente otimizado para analytics/BI)
    # df_tabular.write.mode("overwrite").parquet("data/output/contratacoes_pncp_tabular")
    
    # Exemplo: Converter para Pandas para visualização local rápida (se o dataset não for massivo)
    # pdf = df_tabular.limit(100).toPandas()
    # print(pdf.head())

if __name__ == "__main__":
    main()
    # Fechar a sessão do Spark ao terminar
    spark.stop()