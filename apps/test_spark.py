from pyspark.sql import SparkSession

# Inicializa a sessão do Spark dentro do container
spark = (
    SparkSession.builder.appName("TesteDockerSpark").master("local[*]").getOrCreate()
)

print("\n" + "=" * 50)
print("Sessão Spark Iniciada com Sucesso no Docker!")
print("=" * 50 + "\n")

# Criando um mini DataFrame de exemplo
dados = [("Pregão Eletrônico", "PE"), ("Dispensa", "SP"), ("Inexigibilidade", "RJ")]
colunas = ["Modalidade", "UF"]

df = spark.createDataFrame(dados, schema=colunas)
df.show()

# Fecha a sessão
spark.stop()
