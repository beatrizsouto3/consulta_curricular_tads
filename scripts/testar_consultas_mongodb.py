from pymongo.errors import PyMongoError

from bancos.mongodb.conexao import criar_cliente, obter_banco
from bancos.mongodb.repositorio import RepositorioMongoDB


def main() -> int:
    cliente = criar_cliente()
    try:
        repositorio = RepositorioMongoDB(obter_banco(cliente))
        por_codigo = repositorio.buscar_por_codigo("UFRN-EAJ-TADS-03", "TAD0204")
        por_nome = repositorio.buscar_por_nome("UFRN-EAJ-TADS-03", "CIÊNCIA DE DADOS")
        primeiro_periodo = repositorio.listar_por_periodo("UFRN-EAJ-TADS-03", 1)
        prerequisitos = repositorio.obter_prerequisitos("UFRN-EAJ-TADS-03", "TAD0204")
        estrutura = repositorio.listar_estrutura("UFRN-EAJ-TADS-03")

        assert len(por_codigo) == 1 and por_codigo[0]["codigo"] == "TAD0204"
        assert len(por_nome) == 1 and por_nome[0]["codigo"] == "TAD0204"
        assert len(primeiro_periodo) == 6
        assert len(prerequisitos) == 1
        assert prerequisitos[0]["pre_requisitos"]["operador"] == "AND"
        assert len(estrutura) == 56
        assert repositorio.buscar_por_codigo("UFRN-EAJ-TADS-03", "NAOEXISTE") == []
    except PyMongoError:
        print("Não foi possível executar as consultas. Confira o serviço e a URI do MongoDB.")
        return 1
    finally:
        cliente.close()

    print("Consultas MongoDB funcionando: código, nome, período, pré-requisitos e estrutura.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
