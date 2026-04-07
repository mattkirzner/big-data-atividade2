# from src import Extract
# from src import Load
# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi
from src import ConnectToAtlas as Atlas
from dotenv import load_dotenv
import os
import requests
import json


def consultar_pncp(data_inicial, data_final, modalidade, pagina=1):
    """
    Consulta contratações no PNCP.
    O parâmetro 'modalidade' é OBRIGATÓRIO conforme o erro 400 retornado.
    """
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

    # Parâmetros conforme o manual e a exigência da API
    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "codigoModalidadeContratacao": modalidade,
        "pagina": pagina,
        "tamanhoPagina": 10,
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None


def salvar_em_json(dados, nome_ficheiro="resultado_pncp.json"):
    """Guarda o dicionário 'dados' num ficheiro .json"""
    try:
        with open(nome_ficheiro, "w", encoding="utf-8") as f:
            # indent=4 deixa o ficheiro legível para humanos
            # ensure_ascii=False garante que acentos fiquem corretos
            json.dump(dados, f, indent=4, ensure_ascii=False)
        print(f"Dados guardados com sucesso em: {nome_ficheiro}")
    except Exception as e:
        print(f"Erro ao salvar o ficheiro: {e}")


load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_URL = os.getenv("DB_URL")


def main():
    atlas = Atlas(DB_USER, DB_PASSWORD, DB_URL)

    DB_NAME = "PNCP"
    COL_NAME = "contratacoes"

    # print(atlas.read_data(DB_NAME,COL_NAME,{"numeroControlePNCP":"01612612000106-1-000001/2024"}))

    # atlas.update_by_pncp_id(DB_NAME,COL_NAME, "01612612000106-1-000001/2024", {"orgaoEntidade.razaoSocial":"Onde judas perdeu as botas"})

    atlas.delete_by_pncp_id(DB_NAME, COL_NAME, "01612612000106-1-000001/2024")


if __name__ == "__main__":
    main()
