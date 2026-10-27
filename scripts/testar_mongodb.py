from pymongo.errors import PyMongoError

from bancos.mongodb.conexao import testar_conexao


def main() -> int:
    try:
        testar_conexao()
    except PyMongoError:
        print("Não foi possível conectar ao MongoDB. Confira se o serviço está ativo e a URI está correta.")
        return 1

    print("Conexão com MongoDB funcionando.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
