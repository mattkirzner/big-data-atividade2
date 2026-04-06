import requests


class Extract:

    def __init__(self):
        pass

    def extract_contratacoes_pncp(
        self,
        data_inicial: str,
        data_final: str,
        codigo_modalidade_contratacao: int,
        codigo_modo_disputa: int = None,
        uf: str = None,
        codigo_municipio_ibge: str = None,
    ) -> list[dict]:
        """
        Consulta contratações do PNCP por data de publicação.

        Args:
            data_inicial (str): Data inicial no formato YYYYMMDD.
            data_final (str): Data final no formato YYYYMMDD.
            codigo_modalidade_contratacao (int): Código da modalidade de contratação (obrigatório).
            codigo_modo_disputa (int, optional): Código do modo de disputa.
            uf (str, optional): Sigla do estado (ex: "PE").
            codigo_municipio_ibge (str, optional): Código IBGE do município.

        Returns:
            list[dict]: Lista de contratações encontradas.
        """
        url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
        params = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "codigoModalidadeContratacao": codigo_modalidade_contratacao,
            "pagina": 1,
        }
        if codigo_modo_disputa is not None:
            params["codigoModoDisputa"] = codigo_modo_disputa
        if uf is not None:
            params["uf"] = uf
        if codigo_municipio_ibge is not None:
            params["codigoMunicipioIbge"] = codigo_municipio_ibge

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def extract_country(self, country: str) -> list[dict]:
        """
        Busca universidades em um país, usando a API da Hipo Labs.

        Args:
            country (str): O nome do país, em inglês.

        Returns:
            list[dict]: Uma lista de dicionários onde cada dicionário
            contém informações de uma universidade.
        """
        url = f"http://universities.hipolabs.com/search?country={country}"
        response = requests.get(url)
        response.raise_for_status()
        universities = response.json()

        return universities
