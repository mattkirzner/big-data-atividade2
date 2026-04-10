from src import Extract
from src import Load
from src import Transform
from src import ConnectToAtlas as Atlas
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL = os.getenv("DB_URL")


def main():
    atlas = Atlas(DB_USER, DB_PASSWORD, DB_URL)
    extract = Extract()
    transform = Transform()

    dados = extract.extract_contratacoes_pncp(
        "20250101", "20251231", 6, 1, 50, None, "PE"
    )
    dadosLimpos = transform.filtrar_dados_pncp(dados)

    # print(dadosLimpos)

    DB_NAME = "PNCP"
    COL_NAME = "contratacoesLimpo"

    atlas.upload_pncp_data(DB_NAME, COL_NAME, dadosLimpos)


if __name__ == "__main__":
    main()
