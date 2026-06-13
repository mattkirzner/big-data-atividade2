import os
import sqlite3
import pandas as pd
from fastmcp import FastMCP

mcp = FastMCP("PNCP Data Server")

DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/PNCP_LOCAL.db")
TABLE_NAME = os.getenv("SQLITE_TABLE_NAME", "contratacoes_pncp")


@mcp.tool()
def consultar_banco_pncp(query_sql: str) -> str:
    """
    Executa uma consulta SQL de leitura (SELECT) no banco de dados local do PNCP.
    
    A tabela padrão disponível é configurada dinamicamente e possui o seguinte esquema completo:
    - numeroControlePNCP (TEXT) -> Chave Primária Única do processo
    - data_publicacao (TEXT) -> Data em que a compra foi publicada
    - descricao (TEXT) -> Detalhes explicativos sobre o objeto licitado
    - entidade (TEXT) -> Órgão público ou entidade compradora
    - linkOrigem (TEXT) -> URL externa de origem da contratação
    - modalidade (TEXT) -> Tipo de contratação (ex: Pregão, Dispensa de Licitação)
    - municipio (TEXT) -> Cidade do órgão comprador
    - status (TEXT) -> Situação cadastral do processo (ex: Homologado)
    - uf (TEXT) -> Estado/Unidade Federativa (Sigla de 2 letras, ex: PE, SP)
    - valor (REAL) -> Valor base registrado
    - anoCompra (INTEGER) -> Ano calendário extraído do processo
    """
    query_lower = query_sql.lower()
    if any(
        keyword in query_lower
        for keyword in ["drop", "delete", "insert", "update", "alter", "create"]
    ):
        return "Erro: Apenas consultas de leitura (SELECT) são permitidas."

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query_sql, conn)
        conn.close()

        if df.empty:
            return f"Nenhum resultado encontrado para esta consulta na tabela."
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Erro ao executar SQL: {str(e)}"


if __name__ == "__main__":
    mcp.run()