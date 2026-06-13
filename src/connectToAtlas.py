# essa classe é responsável por fazer conexões com o atlas
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure
from pymongo.errors import PyMongoError
from pymongo import UpdateOne


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

    def upload_pncp_data(self, db_name: str, collection_name: str, json_content):
        """
        Faz upload em lote para o AtlasDB, sem duplicações com base no "numeroControlePNCP".

        Args:
            db_name(str): nome do banco de dados.
            collection_name(str): nome da coleção.
            json_content(list[dict]): lista com os dados a serem inseridos.

        Return:
            list[dict]: uma lista com os ids inseridos.
        """
        try:
            print("Iniciando processo de upload...")

            records = []
            if isinstance(json_content, dict):
                records = json_content.get(
                    "data", [json_content] if json_content else []
                )
            elif isinstance(json_content, list):
                records = json_content

            if not records:
                print("Nenhum registro encontrado para processar.")
                return None

            db = self.client[db_name]
            collection = db[collection_name]

            operacoes = []
            for doc in records:
                id_referencia = doc.get("id") or doc.get("numeroControlePNCP")

                if id_referencia:
                    operacoes.append(
                        UpdateOne(
                            {
                                "numeroControlePNCP": id_referencia
                            },  
                            {
                                "$set": doc,
                            },
                            upsert=True,
                        )
                    )
                else:
    
                    print(f"⚠️ Registro ignorado (sem ID): {str(doc)[:80]}...")

            
            if operacoes:
                print(
                    f"Enviando {len(operacoes)} registros para {db_name}.{collection_name}..."
                )
                result = collection.bulk_write(operacoes)

                print(f"Processamento concluído!")
                print(f"   - Inseridos (Novos): {result.upserted_count}")
                print(f"   - Atualizados (Já existiam): {result.modified_count}")

                return result.upserted_ids
            else:
                print("Nenhuma operação válida gerada.")
                return None

        except Exception as e:
            print(f"Erro no upload para o Atlas: {e}")
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
            query = {"numeroControlePNCP": pncp_id}

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

            result = db[collection_name].delete_one(query)

            if result.deleted_count > 0:
                return f"Sucesso: Registro {pncp_id} removido."
            else:
                return f"Aviso: Registro {pncp_id} não encontrado para exclusão."
        except PyMongoError as e:
            return f"Erro na remoção: {e}"
