from pymongo.errors import PyMongoError

from bancos.mongodb.conexao import criar_cliente, obter_banco
from bancos.mongodb.importacao import carregar_curriculo, importar_curriculo


def main() -> int:
    cliente = criar_cliente()
    try:
        resultado = importar_curriculo(obter_banco(cliente), carregar_curriculo())
    except PyMongoError:
        print("Falha ao importar. Confira se o MongoDB está ativo e a URI está correta.")
        return 1
    finally:
        cliente.close()

    if resultado.upserted_id is not None:
        estado = "inserida"
    elif resultado.modified_count:
        estado = "atualizada"
    else:
        estado = "já estava atualizada"

    print(f"Estrutura {resultado.upserted_id or 'UFRN-EAJ-TADS-03'} {estado}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
