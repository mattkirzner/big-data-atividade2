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

    # Principais códigos de modalidade (conforme Manual de Consultas, seção 5.2):
    # 6: Pregão Eletrônico
    # 8: Dispensa de Licitação
    # 9: Inexigibilidade
    # 10: Manifestação de Interesse

    MODALIDADE = 6  # Vamos testar com Pregão Eletrônico
    DATA_INI = "20240101"
    DATA_FIM = "20240102"

    print(f"Consultando Modalidade {MODALIDADE} entre {DATA_INI} e {DATA_FIM}...")
    resultado = consultar_pncp(DATA_INI, DATA_FIM, MODALIDADE)

    atlas.upload_pncp_data("PNCP", "contratacoes", resultado)

    # if resultado and 'data' in resultado:
    #     for item in resultado['data']:
    #         # Tratamento para evitar o erro de NoneType (subscriptable)
    #         objeto = item.get('objeto') or "Objeto não informado"
    #         numero_pncp = item.get('numeroControlePNCP')

    #         print(f"Número PNCP: {numero_pncp}")
    #         print(f"Objeto: {objeto[:100]}...")
    #         print("-" * 30)
    # else:
    #     print("Nenhum dado encontrado ou erro na resposta.")


if __name__ == "__main__":
    main()
