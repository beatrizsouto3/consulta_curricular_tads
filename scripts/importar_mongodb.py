import sys
from pathlib import Path

from pymongo.errors import PyMongoError

from bancos.curriculo import carregar_curriculo, listar_curriculos
from bancos.mongodb.conexao import criar_cliente, obter_banco
from bancos.mongodb.importacao import importar_curriculo


def main(argumentos: list[str]) -> int:
    caminhos = [Path(argumento) for argumento in argumentos] or listar_curriculos()
    if not caminhos:
        print("Nenhum currículo encontrado em dados/curriculos.")
        return 1

    cliente = criar_cliente()
    try:
        for caminho in caminhos:
            curriculo = carregar_curriculo(caminho)
            resultado = importar_curriculo(obter_banco(cliente), curriculo)
            if resultado.upserted_id is not None:
                estado = "inserida"
            elif resultado.modified_count:
                estado = "atualizada"
            else:
                estado = "já estava atualizada"
            print(f"Estrutura {curriculo['estrutura']['estrutura_id']} {estado}.")
    except PyMongoError:
        print("Falha ao importar. Confira se o MongoDB está ativo e a URI está correta.")
        return 1
    finally:
        cliente.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
