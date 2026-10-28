import sqlite3
import sys
from pathlib import Path

from bancos.curriculo import carregar_curriculo, listar_curriculos
from bancos.sqlite.conexao import criar_conexao, obter_caminho
from bancos.sqlite.importacao import importar_curriculo


def main(argumentos: list[str]) -> int:
    caminhos = [Path(argumento) for argumento in argumentos] or listar_curriculos()
    if not caminhos:
        print("Nenhum currículo encontrado em dados/curriculos.")
        return 1

    conexao = criar_conexao()
    try:
        for caminho in caminhos:
            resumo = importar_curriculo(conexao, carregar_curriculo(caminho))
            print(
                f"Estrutura {resumo['estrutura_id']} importada de {caminho.name}: "
                f"{resumo['componentes']} componentes, "
                f"{resumo['requisitos_integralizacao']} requisitos de integralização."
            )
        print(f"Banco SQLite atualizado em {obter_caminho()}.")
    except sqlite3.Error as erro:
        print(f"Falha ao importar no SQLite: {erro}")
        return 1
    finally:
        conexao.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
