import sqlite3
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

class PNCPSparkPipeline:
    def __init__(self):
        """
        Inicializa o pipeline Spark de forma puramente desacoplada.
        Não possui dependência de conectores ou bancos de dados de origem.
        """
        self.spark = None

    def _init_spark(self, collection_name="Generic"):
        """
        Inicializa a SparkSession local de forma isolada se ela ainda não existir.

        Args:
            collection_name (str): Nome identificador da coleção de dados que batizará
                a aplicação no Spark UI. O padrão é "Generic".
        """
        if not self.spark:
            self.spark = (
                SparkSession.builder.appName(f"Pipeline_{collection_name}")
                .master("local[*]")
                .getOrCreate()
            )

    def clean_raw_data(self, dados_puros):
        """
        1. Limpa e normaliza os dados brutos recebidos externamente.
        Aceita qualquer iterável contendo dicionários mapeados.

        Args:
            dados_puros (iterable): Uma lista ou iterável contendo os dicionários
                (documentos brutos) extraídos da origem (ex: MongoDB).

        Returns:
            list: Uma lista contendo novos dicionários padronizados, com tratamento
                de valores nulos, conversão de tipos e a coluna 'anoCompra' extraída.
        """
        if not dados_puros:
            print("⚠️ Nenhuns dados brutos fornecidos para limpeza.")
            return []

        print("🧹 Limpando chaves e aplicando mapeamento tolerante na memória...")
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

    def process_with_spark(self, dados_tratados, execution_label="PNCP_Process"):
        """
        2. Transforma a lista tipada em RDD/DataFrame Spark e valida o Schema.

        Args:
            dados_tratados (list): Lista de dicionários já normalizados pelo método
                `clean_raw_data`.
            execution_label (str): Rótulo da execução atual utilizado para batizar a
                sessão do Spark. O padrão é "PNCP_Process".

        Returns:
            pandas.DataFrame: Um DataFrame do Pandas estruturado e validado pelo
                motor do PySpark, pronto para ser persistido, ou None se os dados de entrada forem nulos/vazios.
        """
        if not dados_tratados:
            return None

        print(f"📦 {len(dados_tratados)} registros estruturados enviados ao motor Spark...")
        self._init_spark(execution_label)

        schema_defined = StructType([
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
            StructField("anoCompra", IntegerType(), True),
        ])

        self.spark.sparkContext.setJobDescription("Ação: Processamento e validação via Spark")
        df = self.spark.createDataFrame(dados_tratados, schema=schema_defined)

        print("🚀 Estrutura validada com sucesso pelo PySpark:")
        df.printSchema()
        df.show(3, truncate=True)

        df_pandas = df.toPandas()
        self.spark.sparkContext.setJobDescription(None)
        return df_pandas

    def load_to_sqlite(self, df_pandas, sqlite_db_path, sqlite_table_name):
        """
        3. Persistência incremental idempotente (Upsert) no SQLite.

        Args:
            df_pandas (pandas.DataFrame): O DataFrame do Pandas com os dados que serão persistidos.
            sqlite_db_path (str): Caminho físico absoluto ou relativo do arquivo do banco
                de dados SQLite (ex: '/app/PNCP_LOCAL.db').
            sqlite_table_name (str): Nome da tabela destino onde os dados serão armazenados.
        """
        if df_pandas is None or df_pandas.empty:
            print("⚠️ Sem dados para persistir no SQLite.")
            return

        print(f"💾 Efetuando Upsert em: {sqlite_db_path} -> Tabela: {sqlite_table_name}")

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
                anoCompra INTEGER
            )
        """)

        staging_name = f"staging_{sqlite_table_name}"
        df_pandas.to_sql(name=staging_name, con=conexao, if_exists="replace", index=False)

        cursor.execute(f"""
            INSERT OR REPLACE INTO {sqlite_table_name} (
                numeroControlePNCP, data_publicacao, descricao, entidade, linkOrigem, 
                modalidade, municipio, status, uf, valor, anoCompra
            )
            SELECT 
                numeroControlePNCP, data_publicacao, descricao, entidade, linkOrigem, 
                modalidade, municipio, status, uf, valor, anoCompra
            FROM {staging_name}
        """)

        cursor.execute(f"DROP TABLE IF EXISTS {staging_name}")
        conexao.commit()
        conexao.close()
        print(f"🏁 Dados sincronizados na tabela '{sqlite_table_name}' com sucesso!")

    def stop(self):
        """
        Libera recursos da JVM ocupados pelo Spark.
        Encerra e limpa a SparkSession ativa localmente.
        """
        if self.spark:
            print("🛑 Encerrando a sessão do Spark de forma limpa...")
            self.spark.stop()
            self.spark = None