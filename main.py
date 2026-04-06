from src import Extract
from src import Load


def main():
    extract = Extract()
    load = Load()

    ch = extract.extract_country("China")
    load.create_sqlite_table(ch, "universities", "universidades_ch")

    resultado = extract.extract_contratacoes_pncp(
        data_inicial="20240101",
        data_final="20240131",
        codigo_modalidade_contratacao=8,
        uf="PE"
    )
    print(type(resultado))
    print(resultado)


if __name__ == "__main__":
    main()
