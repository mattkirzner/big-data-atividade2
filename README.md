# 📊 Data Engineering & GenAI: PNCP Hybrid Pipeline & Local Chatbot

## ❓ Sobre o Projeto

Este repositório contém uma solução de **Engenharia de Dados ponta a ponta** para ingestão, processamento analítico e consumo inteligente de dados semiestruturados (JSON) provenientes do **PNCP (Portal Nacional de Contratações Públicas)**.

### 🔄 Evolução da Arquitetura

Originalmente focado apenas na ingestão e persistência de dados brutos e refinados no **MongoDB Atlas** utilizando Python nativo, o projeto evoluiu para uma **Arquitetura Híbrida Moderna**.

O ecossistema agora combina:

- ⚡ **PySpark** para processamento distribuído de dados;
- 🎯 **Prefect** para orquestração dos pipelines;
- 🗄️ **MongoDB Atlas** para armazenamento da camada *Raw*;
- 📊 **SQLite** para consultas analíticas locais;
- 🤖 **Ollama + Llama 3.1** para IA Generativa local;
- 🔗 **FastMCP** para integração entre o modelo de linguagem e o banco de dados;
- 🌐 **Streamlit** para interface conversacional.

---

## 🏗️ Arquitetura da Solução

```text
[API do PNCP]
       │
       ▼
[Prefect Orquestrador]
       │
       ▼
[MongoDB Atlas (Raw)]
       │
       ▼
[PySpark Engine (Tratamento)]
       │
       ▼
[SQLite Local]
       │
       ▼
[Llama 3.1 + FastMCP]
       │
       ▼
[Streamlit Chatbot]
```

### Fluxo de Dados

#### 1️⃣ Ingestão (Cérebro Leve)

O **Prefect** gerencia a extração dos dados da API do PNCP e armazena os documentos JSON brutos na camada **Raw** do MongoDB Atlas.

#### 2️⃣ Processamento Analítico (Músculo Pesado)

O **PySpark** realiza:

- Leitura dos dados do Atlas;
- Aplicação de esquemas rígidos (`StructType`);
- Tratamento de valores nulos;
- Padronização de campos;
- Higienização de estruturas dinâmicas.

#### 3️⃣ Persistência Analítica

Os dados processados são convertidos e persistidos em uma base local **SQLite (`PNCP_LOCAL.db`)**, reduzindo custos de infraestrutura e melhorando a velocidade das consultas.

#### 4️⃣ Interface Conversacional (GenAI)

Um aplicativo **Streamlit** se conecta a um servidor **FastMCP**, permitindo que o usuário consulte os dados utilizando linguagem natural.

O modelo **Llama 3.1**, executado localmente via **Ollama**, interpreta as perguntas e consulta o banco quando necessário.

---

## 🚀 Estratégia de Engenharia de Dados e Consistência

### A. Tipagem Estrita e Limpeza com PySpark

Para lidar com inconsistências comuns em APIs governamentais, o pipeline utiliza um esquema rígido:

| Campo | Tipo | Descrição |
|---------|---------|---------|
| `numeroControlePNCP` | StringType | Chave lógica de negócio |
| `uf` | StringType | Unidade Federativa |
| `municipio` | StringType | Município |
| `modalidade` | StringType | Modalidade da compra |
| `valorTotalHomologado` | DoubleType | Valor homologado tratado |
| `anoCompra` | IntegerType | Ano extraído da publicação |

---

### B. Monitoramento com Spark UI

O processamento utiliza anotações customizadas para facilitar a observabilidade.

Isso permite acompanhar:

- Amostragem dos dados;
- Agrupamentos por UF;
- Persistência em SQLite;
- Tempo de execução das operações.

A interface pode ser acessada em:

```text
http://localhost:4040
```

---

## 🤖 Camada de IA Conversacional Local (MCP)

O projeto adota uma abordagem de **Agentic RAG Local**, eliminando dependência de APIs externas pagas.

### Ollama + Llama 3.1

Responsável por:

- Compreender perguntas em linguagem natural;
- Interpretar o contexto dos dados;
- Gerar respostas em português.

### FastMCP (Tool Calling)

O FastMCP expõe ferramentas Python para o modelo de linguagem.

Quando necessário, o Llama:

1. Decide consultar o banco;
2. Gera uma consulta SQL;
3. Executa a consulta no SQLite;
4. Interpreta os resultados;
5. Retorna uma resposta amigável ao usuário.

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologia |
|------------|------------|
| Linguagem | Python 3.11 |
| Processamento | PySpark 3.5 |
| Orquestração | Prefect |
| Banco NoSQL | MongoDB Atlas |
| Driver MongoDB | PyMongo |
| Banco Analítico | SQLite3 |
| Manipulação de Dados | Pandas |
| Interface Web | Streamlit |
| Protocolo de IA | FastMCP |
| IA Local | Ollama |
| Modelo LLM | Llama 3.1 |
| Containers | Docker & Docker Compose |

---

## 📦 Como Executar o Projeto

### 1. Pré-requisitos

Instale:

- Docker
- Docker Compose
- Ollama

Depois baixe o modelo utilizado:

```bash
ollama run llama3.1
```

### 2. Configuração das Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_URL=seu_cluster.mongodb.net
```

### 3. Construção e Inicialização dos Containers

```bash
docker compose up -d --build
```

### 4. Executar o Pipeline Spark

```bash
docker exec -it pyspark_container spark-submit /app/spark_pncp.py
```

### 5. Inicializar o Chatbot Conversacional

```bash
docker exec -it pyspark_container streamlit run /app/app_chatbot_llama3.py --server.address=0.0.0.0
```

### 6. Acessar a Aplicação

```text
http://localhost:8501
```

---

## 📂 Estrutura Geral do Projeto

```text
.
├── app_chatbot_llama3.py
├── processa_pncp2.py
├── docker-compose.yml
├── .env
├── PNCP_LOCAL.db
├── requirements.txt
└── README.md
```

---

## 👥 Equipe

- Allan Ronald Vasconcelos
- Matheus Rangel Kirzner
- Júlia Oliveira Veríssimo

---

## 📜 Licença

Este projeto está licenciado sob a licença **MIT**.

Consulte o arquivo `LICENSE` para mais informações.
