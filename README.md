# | 📊 Data Engineering Challenge: JSON to Relational Persistence
Projeto desenvolvido pela disciplina de Engenharia de Dados e Big Data. Este repositório contém a solução para o desafio de persistência de dados em larga escala, focado na transição de dados semiestruturados (JSON) para um ambiente relacional robusto (SQL). O projeto foi desenvolvido sob a ótica de um Desenvolvedor de Software e Analista de Sistemas, visando escalabilidade e integridade.

📝 O Problema
O cenário proposto envolve o consumo de uma API que fornece dados globais. O desafio consiste em:

Modelar um esquema de banco de dados eficiente.

Estrategizar a ingestão de dados de múltiplos países, garantindo que o sistema não se torne um "pesadelo de manutenção" à medida que o volume cresce.

🛠️ 1. Modelagem de Dados
Para garantir a normalização e evitar a redundância, propomos um modelo dividido em duas tabelas principais. Esta estrutura permite que informações estáticas dos países fiquem separadas das métricas voláteis.

🚀 2. Estratégia de Ingestão e Consistência
Lidar com dados de vários países exige uma estratégia que equilibre desempenho de escrita e velocidade de leitura. Abaixo, detalho a abordagem recomendada:

A. Particionamento de Dados
Para garantir a performance de consulta em um histórico longo, a melhor estratégia é o Particionamento de Tabelas por Lista (List Partitioning) baseado no country_code ou por Intervalo (Range) baseado na reference_date.

Vantagem: Consultas filtradas por país ou período realizarão o partition pruning, lendo apenas os arquivos/setores necessários no disco.

B. Estratégia "Upsert" (Idempotência)
Como APIs podem ser chamadas múltiplas vezes para o mesmo período, utilizamos a lógica de UPSERT (Insert on Conflict Update).

Isso garante que, se os dados de um país para uma data específica forem reprocessados, o registro existente será atualizado em vez de duplicado, mantendo a consistência do histórico.

C. Camada de Stage (Staging Area)
Antes de persistir na tabela final, os dados do JSON são carregados em uma tabela temporária de "Stage".

Validação: Verificamos tipos de dados e valores nulos.

Enriquecimento: Validamos se o country_code já existe na dim_countries.

Carga: Movemos os dados validados para a fact_indicators.

D. Manutenibilidade e Escalabilidade
Indexação: Criação de índices B-Tree no campo reference_date e índices compostos em (country_code, indicator_name).

Paralelismo: A ingestão pode ser feita em threads separadas por região geográfica, acelerando o processo de carga sem travar a tabela inteira.

🛠️ Tecnologias Sugeridas
Linguagem: Python (Pandas/SQLAlchemy) para o parser do JSON.

Banco de Dados: PostgreSQL (pelo suporte nativo a JSONB e particionamento).

Orquestração: Airflow ou Prefect (para agendar as extrações da API).

Dica de Analista: Em cenários de Big Data, se o volume de países e indicadores crescer exponencialmente, considere evoluir essa modelagem para um Data Lakehouse, onde o JSON bruto é armazenado em camadas (Bronze) e a modelagem relacional reside na camada de consumo (Gold).

## 👥 | Equipe

- Allan Ronald Vasconcelos
- Matheus Rangel Kirzner
- Julia Oliveira Veríssimo


***

## 📜 | Licença 

Este projeto está licenciado sob a licença MIT.
