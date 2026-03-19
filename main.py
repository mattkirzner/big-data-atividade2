from src import Extract
from src import Load


def main():
    extract = Extract()
    load = Load()

    ch = extract.extract_country("China")
    load.create_sqlite_table(ch, "universities", "universidades_ch")


if __name__ == "__main__":
    main()
