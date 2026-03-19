import sqlite3


class Load:
    def __init__(self):
        pass

    def create_sqlite_table(
        self, universities_list: list[dict], db_name: str, table_name: str
    ):
        """
        Método responsável por criar o banco SQL e adicionar tabelas e dados.

        Args:
            universities_list (list): Lista de dicionários contendo informações das universidades.
            db_name (str): Nome do banco de dados a ser criado.
            table_name (str): Nome da tabela a ser criada no banco de dados.
        """
        # Criar o banco e se concectar nele
        # Criar o banco e se concectar nele
        con = sqlite3.connect(f"{db_name}.db")
        c = con.cursor()

        c.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
        id INTERGER PRIMARY KEY,
        name TEXT,
        country TEXT,
        state_province TEXT,
        web_pages TEXT,
        domains TEXT
        );
        """)

        for university in universities_list:
            c.execute(
                f"""INSERT INTO {table_name} (name, country, state_province,
            web_pages, domains) VALUES (?,?,?,?,?);""",
                (
                    university.get("name"),
                    university.get("country"),
                    university.get("state-province"),
                    ", ".join(university.get("web_pages", [])),
                    ", ".join(university.get("domains", [])),
                ),
            )

        con.commit()
        con.close()
