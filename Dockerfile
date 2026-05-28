# 1. Imagem base oficial e leve com Python 3.11
FROM python:3.11-slim-bullseye

# 2. Instala o Java (JDK 11) necessário obrigatoriamente para o motor core do PySpark
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk-headless \
    && rm -rf /var/lib/apt/lists/*

# 3. Configura as variáveis de ambiente essenciais para o Java
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# 4. Instala o PySpark, PyMongo (com suporte a DNS srv) e o Python-Dotenv
RUN pip install --no-cache-dir \
    pyspark==3.5.0 \
    pymongo[srv]==4.6.1 \
    python-dotenv \
    pandas \
    streamlit \
    openai \
    fastmcp \
    tabulate

# 5. Define o diretório de trabalho padrão dentro do container
WORKDIR /app

# 6. Mantém o container ativo em segundo plano aguardando execuções
CMD ["tail", "-f", "/dev/null"]