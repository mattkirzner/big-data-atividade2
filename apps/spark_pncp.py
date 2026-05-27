from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from connectToAtlas import ConnectToAtlas # Ligação com a pasta src feita pelo docker compose
import os
import sqlite3

# 1. Resgata as variáveis de ambiente
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL = os.getenv("DB_URL")

print("🔌 Conectando ao MongoDB Atlas via PyMongo...")
atlas = ConnectToAtlas(user=DB_USER, password=DB_PASSWORD, url=DB_URL)
dados_puros = atlas.read_data(db_name="PNCP", collection_name="prefect_teste")

# 🔍 DIAGNÓSTICO: Mostra exatamente como as chaves vieram do Atlas no primeiro registo
if dados_puros:
    print("\n🔬 [DIAGNÓSTICO] Chaves reais detetadas no primeiro documento do MongoDB:")
    print(dados_puros[0].keys())
    print("----------------------------------------------------------------------\n")

print("🧹 Limpando chaves e mapeando dicionários de forma tolerante...")
dados_tratados = []
for doc in dados_puros:
    doc_limpo = {}
    
    # 💡 Mapeamento tolerante: Procura variações comuns de nomes que possam vir da API do PNCP
    # Se no Mongo estiver diferente, adicionamos aqui a alternativa correspondente
    
    doc_limpo["numeroControlePNCP"] = doc.get("numeroControlePNCP") or ""
    doc_limpo["uf"] = doc.get("uf") or ""
    doc_limpo["municipio"] = doc.get("municipio") or ""
    doc_limpo["modalidade"] = doc.get("modalidade") or ""
    
    # 💡 CORRIGIDO: No seu Mongo a chave chama-se 'valor'
    v_total = doc.get("valor")
    if v_total is not None:
        try:
            doc_limpo["valorTotalHomologado"] = float(v_total)
        except (ValueError, TypeError):
            doc_limpo["valorTotalHomologado"] = 0.0
    else:
        doc_limpo["valorTotalHomologado"] = 0.0

    # 💡 CORRIGIDO: Como não há 'anoCompra', vamos extrair o ano da 'data_publicacao'
    data_pub = doc.get("data_publicacao")  # Ex: "2025-02-15..."
    if data_pub and len(str(data_pub)) >= 4:
        try:
            doc_limpo["anoCompra"] = int(str(data_pub)[:4]) # Pega os 4 primeiros dígitos (Ano)
        except (ValueError, TypeError):
            doc_limpo["anoCompra"] = 0
    else:
        doc_limpo["anoCompra"] = 0
            
    dados_tratados.append(doc_limpo)

print(f"📦 {len(dados_tratados)} registos prontos. Inicializando motor Spark...")

# 3. Inicializa uma SparkSession pura
spark = SparkSession.builder \
    .appName("SparkMongoHibrido") \
    .master("local[*]") \
    .getOrCreate()

# Schema rígido com os mesmos nomes exatos que inserimos no doc_limpo acima
schema_definido = StructType([
    StructField("numeroControlePNCP", StringType(), True),
    StructField("uf", StringType(), True),
    StructField("municipio", StringType(), True),
    StructField("modalidade", StringType(), True),
    StructField("valorTotalHomologado", DoubleType(), True), 
    StructField("anoCompra", IntegerType(), True)           
])

# 4. Transforma a lista em Spark DataFrame aplicando o Schema
df = spark.createDataFrame(dados_tratados, schema=schema_definido)

# 5. Exibindo os dados
spark.sparkContext.setJobDescription("Ação: Exibir amostragem de dados do PNCP")
print("🚀 Esquema mapeado com sucesso pelo PySpark:")
df.printSchema()
df.show(5, truncate=False)

spark.sparkContext.setJobDescription("Métrica: Contagem de contratações agrupadas por UF")
print("📊 Contagem de contratações por UF:")
df.groupBy("uf").count().show()

spark.sparkContext.setJobDescription("Persistência: Gravando dados tratados no SQLite local")

# O caminho "/app" está mapeado no seu docker-compose.yml para a pasta local "./apps"
caminho_banco_local = "/app/PNCP_LOCAL.db"
print(f"💾 Salvando dados estruturados localmente em: {caminho_banco_local}...")

# Convertemos o Spark DataFrame final para Pandas para salvar de forma simples no SQLite
df_pandas = df.toPandas()

# Estabelece a conexão com o arquivo de banco e grava os dados substituindo caso a tabela já exista
conexao = sqlite3.connect(caminho_banco_local)
df_pandas.to_sql(name="contratacoes_pncp", con=conexao, if_exists="replace", index=False)
conexao.close()

print("🏁 Gravação concluída com sucesso!")

# Remove as descrições de Job para limpar o contexto do Spark
spark.sparkContext.setJobDescription(None)

print("🌐 Acesse o Spark UI em: http://localhost:4040")
print("⌨️  Pressione ENTER no terminal para encerrar o script...")
input()

spark.stop()