from fastmcp import FastMCP
import sqlite3
import pandas as pd

# Inicializa o servidor MCP dedicado ao PNCP
mcp = FastMCP("PNCP Data Server")

DB_PATH = "/app/PNCP_LOCAL.db"


@mcp.tool()
def consultar_banco_pncp(query_sql: str) -> str:
    """
    Executa uma consulta SQL de leitura (SELECT) no banco de dados local do PNCP.
    A tabela disponível é 'contratacoes_pncp' com as colunas:
    - numeroControlePNCP (TEXT)
    - uf (TEXT)
    - municipio (TEXT)
    - modalidade (TEXT)
    - valorTotalHomologado (REAL)
    - anoCompra (INTEGER)
    """
    # Proteção simples contra comandos de escrita
    query_lower = query_sql.lower()
    if any(
        keyword in query_lower
        for keyword in ["drop", "delete", "insert", "update", "alter"]
    ):
        return "Erro: Apenas consultas de leitura (SELECT) são permitidas."

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query_sql, conn)
        conn.close()

        if df.empty:
            return "Nenhum resultado encontrado para esta consulta."
        return df.to_markdown(index=False)
    except Exception as e:
        return f"Erro ao executar SQL: {str(e)}"


if __name__ == "__main__":
    # Inicia o servidor em modo de desenvolvimento
    mcp.run()
