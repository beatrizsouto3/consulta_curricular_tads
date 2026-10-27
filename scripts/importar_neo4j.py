import sys
from pathlib import Path

from neo4j.exceptions import DriverError, Neo4jError

from bancos.curriculo import carregar_curriculo, listar_curriculos
from bancos.neo4j.conexao import criar_driver, obter_nome_banco
from bancos.neo4j.importacao import importar_curriculo


def main(argumentos: list[str]) -> int:
    caminhos = [Path(argumento) for argumento in argumentos] or listar_curriculos()
    if not caminhos:
        print("Nenhum currículo encontrado em dados/curriculos.")
        return 1

    driver = criar_driver()
    try:
        for caminho in caminhos:
            resumo = importar_curriculo(driver, carregar_curriculo(caminho), obter_nome_banco())
            print(
                f"Estrutura {resumo['estrutura_id']} importada de {caminho.name}: "
                f"{resumo['componentes']} componentes, {resumo['externos']} externos, "
                f"{resumo['grupos']} grupos de requisitos, {resumo['dependencias']} dependências."
            )
    except (DriverError, Neo4jError):
        print("Falha ao importar. Confira se o Neo4j está ativo e as credenciais do .env.")
        return 1
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
