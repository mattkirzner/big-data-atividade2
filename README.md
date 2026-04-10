# 📊 Data Engineering: PNCP JSON to NoSQL Persistence

## ❓ Sobre

Este repositório contém a solução para o desafio de persistência de dados em larga escala, focado na ingestão de dados semiestruturados (JSON) provenientes do **PNCP (Portal Nacional de Contratações Públicas)**.

Originalmente concebido para uma transição relacional, o projeto foi otimizado para uma arquitetura **NoSQL baseada em documentos**, utilizando o **MongoDB Atlas**. Esta abordagem permite lidar com a natureza dinâmica das licitações, garantindo **escalabilidade na nuvem** e **flexibilidade de esquema**.

---

## 📝 O Problema

O cenário envolve o consumo de APIs que fornecem dados complexos de compras públicas. Os principais desafios endereçados são:

- ⚙️ **Gerenciamento de Recursos**: Evitar o esgotamento de conexões no cluster através do padrão *Singleton*.
- 🔁 **Integridade e Idempotência**: Garantir que re-processamentos não gerem duplicidade de registros.
- 🔀 **Polimorfismo de Dados**: Capacidade de processar tanto o JSON bruto (*raw*) quanto dados transformados (*refined*).

---

## 🛠️ 1. Arquitetura de Software

A solução foi construída em **Python**, implementando padrões de projeto para garantir robustez:

- 🧩 **Padrão Singleton**  
  Implementado na classe `ConnectToAtlas` para garantir que apenas uma instância do `MongoClient` seja utilizada em toda a aplicação, otimizando o pool de conexões.

- 🔄 **CRUD Dinâmico**  
  Métodos flexíveis que aceitam nomes de bancos e coleções como argumentos, permitindo que a mesma classe gerencie diferentes fluxos de dados.

- 🔒 **Encapsulamento**  
  Tratamento de erros centralizado e uso de *docstrings* detalhadas para facilitar a manutenção.

---

## 🚀 2. Estratégia de Ingestão e Consistência

Diferente do modelo SQL rígido, adotamos uma estratégia de **Schema-on-Read** e **Refining**.

### A. Camadas de Dados

- 🟡 **Raw Layer (Bruto)**  
  Armazena o JSON completo vindo da API, preservando a fidelidade do dado original.

- 🟢 **Refined Layer (Limpo)**  
  Dados transformados, com campos *flattened* (achatados) e filtrados para facilitar a visualização no front-end e dashboards.

---

### B. Estratégia "Upsert" (A ser implementado)

Para evitar duplicidade, utilizamos o campo de negócio `numeroControlePNCP` como chave primária lógica.

- ♻️ **Idempotência**  
  As funções de upload verificam a existência do ID único.

- 🔄 **Consistência**  
  Atualização de registros existentes em vez de criação de novos, mantendo o histórico limpo.

---

### C. Otimização de Performance

- 📦 **Inserção em Lote (Bulk Insert)**  
  Uso de `insert_many` para reduzir o tráfego de rede com o cluster Atlas.

- ⚡ **Indexação**  
  Recomendação de índices únicos no campo `numeroControlePNCP` para garantir buscas instantâneas.

---

## 🛠️ Tecnologias Utilizadas

- 🐍 **Linguagem**: Python 3.x  
- 🍃 **Banco de Dados**: MongoDB Atlas  
- 🔌 **Driver**: PyMongo  
- 📄 **Formatos**: JSON / BSON  

---

## 👥 Equipe

- Allan Ronald Vasconcelos  
- Matheus Rangel Kirzner  
- Júlia Oliveira Veríssimo  

---

## 📜 Licença

Este projeto está licenciado sob a licença **MIT**.  
Veja o arquivo `LICENSE` para mais detalhes.
