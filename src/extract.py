import requests


class Extract:

    def __init__(self):
        pass

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
