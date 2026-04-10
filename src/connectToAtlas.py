# essa classe é responsável por fazer conexões com o atlas
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure
from pymongo.errors import PyMongoError


class ConnectToAtlas:
    _instance = None
    _client = None

    def __new__(cls, user: str, password: str, url: str):
        """
        Gerenciador Singleton para operações no MongoDB Atlas.

        Esta classe garante que apenas uma conexão com o cluster seja mantida
        ativa, otimizando o uso de recursos e performance.
        """

        if cls._instance is None:
            cls._instance = super(ConnectToAtlas, cls).__new__(cls)

            uri = f"mongodb+srv://{user}:{password}@{url}"
            try:
                cls._client = MongoClient(uri, server_api=ServerApi("1"))
                cls._client.admin.command("ping")
                print("Instância única do MongoDB Atlas criada!")
            except ConnectionFailure as e:
                cls._instance = None  # Reseta se falhar na primeira vez
                raise Exception(f"Falha ao conectar: {e}")

        return cls._instance

    def __init__(self, user: str, password: str, url: str):
        """
        Inicializa a conexão com o MongoDB Atlas.

        Args:
            user (str): Nome de usuário do banco de dados (configurado no Database Access).
            password (str): Senha do usuário. Note que caracteres especiais devem estar URL-encoded.
            url (str): Endereço do cluster (ex: 'cluster0.XXXXXXX.mongodb.net/?appName=Cluster0').
                      Não deve incluir o prefixo 'mongodb+srv://'.
        """
        self.client = self._client

    def upload_pncp_data(self, db_name: str, collection_name: str, json_content: dict):
        """
        Extrai a lista de 'data' do JSON do PNCP e faz o upload em lote para o AtlasDB.

        Args:
            db_name(str): nome do banco de dados.
            collection_name(str): nome da coleção.
            json_content(list[dict]): lista com os dados a serem inseridos.

        Return:
            list[dict]: uma lista com os ids inseridos.
        """

        try:
            # Extraímos apenas a lista de registros
            # records = json_content.get("data", [])

            if isinstance(json_content, dict) and "data" in json_content:
                records = json_content.get("data", [])

            # Se já for uma lista (dados limpos), usamos diretamente.
            elif isinstance(json_content, list):
                records = json_content

            # Caso contrário (ex: dicionário sem chave 'data'), tratamos como um único registro.
            elif isinstance(json_content, dict):
                records = [json_content]

            else:
                print("Formato de dados inválido.")
                return None

            if not records:
                print("Nenhum registro encontrado para upload.")
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

    def read_data(
        self, db_name: str, collection_name: str, query: dict = None, limit: int = 0
    ):
        """
        Busca documentos baseados em um filtro.

        Args:
            db_name (str): Nome do banco de dados no Atlas.
            collection_name(str): nome da coleção.
            query (dict, optional): Filtro de busca no formato MONGODB.
                Exemplo de query: {"orgaoEntidade.cnpj": "01612612000106"}
                Se não fornecido, retorna todos os documentos. Defaults to None.
            limit (int, optional): Número máximo de documentos a retornar.
                Não usar retorna todos os documentos encontrados.
                Defaults to 0.

        Returns:
            list[dict]: lista com os documentos encontrado.
        """
        try:
            db = self.client[db_name]
            # O limit(0) no PyMongo retorna todos os documentos
            cursor = db[collection_name].find(query or {}).limit(limit)
            return list(cursor)
        except PyMongoError as e:
            print(f"Erro na leitura: {e}")
            return []

    def update_by_pncp_id(
        self, db_name: str, collection_name: str, pncp_id: str, new_data: dict
    ):
        """
        Atualiza um registro específico usando o numeroControlePNCP.

        Args:
            db_name(str): nome do banco de dados.
            collection_name(str): nome da coleção.
            pncp_id(str): id do numeroControlePNCP.
            new_data(list[dict]): query a ser atualizada
                (ex: {"orgaoEntidade.razaoSocial":"Cesar School"}).

        Returns:
            (str): mensagem com o resultado da operação.
        """
        try:
            db = self.client[db_name]
            # O filtro é fixo no identificador único
            query = {"numeroControlePNCP": pncp_id}

            # Usamos update_one para garantir que apenas um registro seja afetado
            result = db[collection_name].update_one(query, {"$set": new_data})

            if result.matched_count > 0:
                return f"Sucesso: Registro {pncp_id} atualizado."
            else:
                return f"Aviso: Nenhum registro encontrado com o ID {pncp_id}."
        except PyMongoError as e:
            return f"Erro no update: {e}"

    def delete_by_pncp_id(self, db_name: str, collection_name: str, pncp_id: str):
        """
        Remove um registro específico usando o numeroControlePNCP.

        Args:
            db_name(str): nome do banco de dados.
            collection_name(str): nome da coleção.
            pncp_id(str): id do numeroControlePNCP.

        Returns:
            (str): mensagem com o resultado da operação.
        """
        try:
            db = self.client[db_name]
            query = {"numeroControlePNCP": pncp_id}

            # delete_one é mais seguro aqui para evitar remoções em massa
            result = db[collection_name].delete_one(query)

            if result.deleted_count > 0:
                return f"Sucesso: Registro {pncp_id} removido."
            else:
                return f"Aviso: Registro {pncp_id} não encontrado para exclusão."
        except PyMongoError as e:
            return f"Erro na remoção: {e}"
