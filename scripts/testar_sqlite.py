import sqlite3

from bancos.sqlite.conexao import obter_caminho, testar_conexao


def main() -> int:
    try:
        testar_conexao()
    except sqlite3.Error as erro:
        print(f"Não foi possível abrir o banco SQLite: {erro}")
        return 1

    print(f"Conexão com SQLite funcionando em {obter_caminho()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
