import os
import sqlite3
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    IntegerType,
)
from connectToAtlas import ConnectToAtlas


class PNCPSparkPipeline:
    def __init__(self, atlas_connection):
        """
        Inicializa o pipeline com os parâmetros dinâmicos de origem (Atlas) e destino (SQLite).

        Args:
            atlas_connection (ConnectToAtlas): Instância configurada do objeto de conexão
                customizado para o MongoDB Atlas.
        """
        self.atlas = atlas_connection
        self.spark = None

    def _init_spark(self, collection_name="Generic"):
        """
        Método interno corrigido para inicializar a SparkSession com o nome dinâmico.

        Args:
            collection_name (str, optional): Nome da coleção do MongoDB que batizará a
                aplicação no Spark UI. O valor padrão é "Generic".
        """
        if not self.spark:
            self.spark = (
                SparkSession.builder.appName(f"Pipeline_{collection_name}")
                .master("local[*]")
                .getOrCreate()
            )

    def extract_and_clean(self, db_name, collection_name):
        """
        1. Extrai os dados do MongoDB Atlas e limpa as chaves (sem _id e id).

        Args:
            db_name (str): Nome do banco de dados alvo no MongoDB Atlas.
            collection_name (str): Nome da coleção que contém os documentos brutos no MongoDB Atlas.

        Returns:
            list: Uma lista de dicionários Python purificados e padronizados, pronta para o Spark.
        """
        print(
            f"🔌 Lendo dados da coleção '{collection_name}' na base de dados '{db_name}'..."
        )
        dados_puros = self.atlas.read_data(
            db_name=db_name, collection_name=collection_name
        )

        if not dados_puros:
            print("⚠️ Nenhum dado bruto encontrado no MongoDB Atlas.")
            return []

        print("🧹 Limpando chaves e aplicando mapeamento tolerante...")
        dados_tratados = []
        for doc in dados_puros:
            doc_limpo = {}

            numero_controle = doc.get("numeroControlePNCP")
            doc_limpo["numeroControlePNCP"] = (
                str(numero_controle).strip() if numero_controle else ""
            )
            doc_limpo["data_publicacao"] = doc.get("data_publicacao") or ""
            doc_limpo["descricao"] = doc.get("descricao") or ""
            doc_limpo["entidade"] = doc.get("entidade") or ""
            doc_limpo["linkOrigem"] = doc.get("linkOrigem") or ""
            doc_limpo["status"] = doc.get("status") or ""
            doc_limpo["modalidade"] = doc.get("modalidade") or ""
            doc_limpo["municipio"] = doc.get("municipio") or ""
            doc_limpo["uf"] = doc.get("uf") or ""

            v_total = doc.get("valor")
            if v_total is not None:
                try:
                    doc_limpo["valor"] = float(v_total)
                except (ValueError, TypeError):
                    doc_limpo["valor"] = 0.0
            else:
                doc_limpo["valor"] = 0.0

            doc_limpo["valorTotalHomologado"] = doc_limpo["valor"]

            if (
                doc_limpo["data_publicacao"]
                and len(str(doc_limpo["data_publicacao"])) >= 4
            ):
                try:
                    doc_limpo["anoCompra"] = int(str(doc_limpo["data_publicacao"])[:4])
                except (ValueError, TypeError):
                    doc_limpo["anoCompra"] = 0
            else:
                doc_limpo["anoCompra"] = 0

            dados_tratados.append(doc_limpo)

        return dados_tratados

    def process_with_spark(self, dados_tratados, collection_name="PNCP"):
        """
        2. Inicializa o Spark de forma segura, valida o Schema estrito e converte para Pandas.

        Args:
            dados_tratados (list): Lista de dicionários vindos do método 'extract_and_clean'.
            collection_name (str, optional): Nome da coleção para batizar o processo Spark.
                O valor padrão é "PNCP".

        Returns:
            pandas.DataFrame: DataFrame do Pandas convertido e tipado de acordo com o Schema estrito,
                ou None se a entrada estiver vazia.
        """
        if not dados_tratados:
            return None

        print(
            f"📦 {len(dados_tratados)} registos estruturados. Inicializando motor Spark..."
        )
        self._init_spark(collection_name)

        schema_defined = StructType(
            [
                StructField("numeroControlePNCP", StringType(), True),
                StructField("data_publicacao", StringType(), True),
                StructField("descricao", StringType(), True),
                StructField("entidade", StringType(), True),
                StructField("linkOrigem", StringType(), True),
                StructField("modalidade", StringType(), True),
                StructField("municipio", StringType(), True),
                StructField("status", StringType(), True),
                StructField("uf", StringType(), True),
                StructField("valor", DoubleType(), True),
                StructField("valorTotalHomologado", DoubleType(), True),
                StructField("anoCompra", IntegerType(), True),
            ]
        )

        self.spark.sparkContext.setJobDescription(
            "Ação: Processamento e amostragem de dados via Spark"
        )
        df = self.spark.createDataFrame(dados_tratados, schema=schema_defined)

        print("🚀 Estrutura validada com sucesso pelo PySpark:")
        df.printSchema()
        df.show(3, truncate=True)

        df_pandas = df.toPandas()
        self.spark.sparkContext.setJobDescription(None)
        return df_pandas

    def load_to_sqlite(self, df_pandas, sqlite_db_path, sqlite_table_name):
        """
        3. Realiza a persistência incremental (Upsert) dinâmica no SQLite local.

        Args:
            df_pandas (pandas.DataFrame): DataFrame do Pandas retornado pelo processamento do Spark.
            sqlite_db_path (str): Caminho absoluto de destino do arquivo do banco SQLite (ex: '/app/PNCP_LOCAL.db').
            sqlite_table_name (str): Nome da tabela final onde os dados serão armazenados de forma incremental.
        """
        if df_pandas is None or df_pandas.empty:
            print("⚠️ Sem dados para gravar no SQLite.")
            return

        print(
            f"💾 Processando Upsert local em: {sqlite_db_path} -> Tabela: {sqlite_table_name}"
        )

        conexao = sqlite3.connect(sqlite_db_path)
        cursor = conexao.cursor()

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {sqlite_table_name} (
                numeroControlePNCP TEXT PRIMARY KEY,
                data_publicacao TEXT,
                descricao TEXT,
                entidade TEXT,
                linkOrigem TEXT,
                modalidade TEXT,
                municipio TEXT,
                status TEXT,
                uf TEXT,
                valor REAL,
                valorTotalHomologado REAL,
                anoCompra INTEGER
            )
        """)

        staging_name = f"staging_{sqlite_table_name}"

        df_pandas.to_sql(
            name=staging_name, con=conexao, if_exists="replace", index=False
        )

        cursor.execute(f"""
            INSERT OR REPLACE INTO {sqlite_table_name} (
                numeroControlePNCP, data_publicacao, descricao, entidade, linkOrigem, 
                modalidade, municipio, status, uf, valor, valorTotalHomologado, anoCompra
            )
            SELECT 
                numeroControlePNCP, data_publicacao, descricao, entity = entidade, linkOrigem, 
                modalidade, municipio, status, uf, valor, valorTotalHomologado, anoCompra
            FROM {staging_name}
        """.replace("entity = entidade", "entidade"))

        cursor.execute(f"DROP TABLE IF EXISTS {staging_name}")

        conexao.commit()
        conexao.close()
        print(
            f"🏁 Tabela '{sqlite_table_name}' atualizada com sucesso de forma incremental!"
        )

    def stop(self):
        """
        Fecha a sessão do Spark libertando os recursos do sistema.
        """
        if self.spark:
            print("🛑 Encerrando a sessão do Spark de forma limpa...")
            self.spark.stop()
            self.spark = None
