from neo4j.exceptions import DriverError, Neo4jError

from bancos.neo4j.conexao import criar_driver, obter_nome_banco
from bancos.neo4j.repositorio import RepositorioNeo4j


def main() -> int:
    driver = criar_driver()
    try:
        repositorio = RepositorioNeo4j(driver, obter_nome_banco())
        por_codigo = repositorio.buscar_por_codigo("UFRN-EAJ-TADS-03", "TAD0204")
        por_nome = repositorio.buscar_por_nome("UFRN-EAJ-TADS-03", "CIÊNCIA DE DADOS")
        primeiro_periodo = repositorio.listar_por_periodo("UFRN-EAJ-TADS-03", 1)
        prerequisitos = repositorio.obter_prerequisitos("UFRN-EAJ-TADS-03", "TAD0204")
        estrutura = repositorio.listar_estrutura("UFRN-EAJ-TADS-03")
        cadeia = repositorio.listar_cadeia_pre_requisitos("UFRN-EAJ-TADS-03", "TAD0204")

        assert len(por_codigo) == 1 and por_codigo[0]["codigo"] == "TAD0204"
        assert len(por_nome) == 1 and por_nome[0]["codigo"] == "TAD0204"
        assert len(primeiro_periodo) == 6
        assert len(prerequisitos) == 1
        assert prerequisitos[0]["pre_requisitos"]["operador"] == "AND"
        assert len(estrutura) == 56
        assert {"TAD0022", "TAD0102", "TAD0002"} <= {item["codigo"] for item in cadeia}
        assert repositorio.buscar_por_codigo("UFRN-EAJ-TADS-03", "NAOEXISTE") == []
    except (DriverError, Neo4jError):
        print("Não foi possível executar as consultas. Confira o serviço e as credenciais do Neo4j.")
        return 1
    finally:
        driver.close()

    print("Consultas Neo4j funcionando: código, nome, período, pré-requisitos, estrutura e cadeia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
