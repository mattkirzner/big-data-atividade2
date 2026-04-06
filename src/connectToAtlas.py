# essa classe é responsável por fazer conexões com o atlas
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure


class ConnectToAtlas:
    # Atributo de classe para armazenar a única instância
    _instance = None
    _client = None

    def __new__(cls, user: str, password: str, url: str):
        # Se a instância ainda não existe, cria ela
        if cls._instance is None:
            cls._instance = super(ConnectToAtlas, cls).__new__(cls)

            # Monta a URI e cria o client apenas uma vez
            uri = f"mongodb+srv://{user}:{password}@{url}"
            try:
                cls._client = MongoClient(uri, server_api=ServerApi("1"))
                # Opcional: Testa a conexão imediatamente
                cls._client.admin.command("ping")
                print("Instância única do MongoDB Atlas criada!")
            except ConnectionFailure as e:
                cls._instance = None  # Reseta se falhar na primeira vez
                raise Exception(f"Falha ao conectar: {e}")

        return cls._instance

    def __init__(self, user: str, password: str, url: str):
        self.client = self._client

    def upload_pncp_data(self, db_name: str, collection_name: str, json_content: dict):
        """
        Extrai a lista de 'data' do JSON e faz o upload em lote.
        """
        try:
            # Extraímos apenas a lista de registros
            records = json_content.get("data", [])

            if not records:
                print("Nenhum dado encontrado para upload.")
                return None

            db = self.client[db_name]
            collection = db[collection_name]

            # insert_many é muito mais rápido para listas
            result = collection.insert_many(records)

            print(f"Sucesso! {len(result.inserted_ids)} documentos inseridos.")
            return result.inserted_ids

        except Exception as e:
            print(f"Erro ao subir dados para o Atlas: {e}")
            return None

    def getMovieByTitle(self, dbName: str, collectionName: str, movieTitle: str):
        """
        Busca
        """
        db = self.client[dbName]
        collection = db[collectionName]
        achados = collection.find({"title": movieTitle})
        resultado = []

        for filme in achados:
            resultado.append({"nome": filme["title"], "ano": filme["year"]})

        return resultado
