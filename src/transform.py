# Classe responsável por transformar dados antes de fazer o upload
class Transform:
    def __init__(self):
        pass

    def filtrar_dados_pncp(self, json_bruto):
        """
        Transforma o JSON complexo do PNCP em uma lista simplificada.

        Args:
            json_bruto(list[dict]): uma lista das contratações do PNCP

        Returns:
            list[dict]: uma lista com a simplificação dos dados obtidos
        """
        dados_simplificados = []

        for item in json_bruto.get("data", []):
            # Criamos um dicionário apenas com o essencial
            resumo = {
                "id": item.get("numeroControlePNCP"),
                "entidade": item.get("orgaoEntidade", {}).get("razaoSocial"),
                "municipio": item.get("unidadeOrgao", {}).get("municipioNome"),
                "uf": item.get("unidadeOrgao", {}).get("ufSigla"),
                "descricao": item.get("objetoCompra"),
                "valor": item.get("valorTotalEstimado"),
                "modalidade": item.get("modalidadeNome"),
                "status": item.get("situacaoCompraNome"),
                "linkOrigem": item.get("linkSistemaOrigem"),
                "data_publicacao": item.get("dataPublicacaoPncp")[
                    :10
                ],  # Apenas AAAA-MM-DD
            }
            dados_simplificados.append(resumo)

        return dados_simplificados
