MODELOS = ("MongoDB", "SQLite", "Neo4j")


def criar_repositorio(modelo: str):
    # Imports tardios: um driver ausente não impede o uso dos outros bancos
    if modelo == "MongoDB":
        from bancos.mongodb.conexao import criar_cliente, obter_banco
        from bancos.mongodb.repositorio import RepositorioMongoDB

        return RepositorioMongoDB(obter_banco(criar_cliente()))
    if modelo == "SQLite":
        from bancos.sqlite.conexao import criar_conexao
        from bancos.sqlite.repositorio import RepositorioSQLite

        return RepositorioSQLite(criar_conexao())
    if modelo == "Neo4j":
        from bancos.neo4j.conexao import criar_driver, obter_nome_banco
        from bancos.neo4j.repositorio import RepositorioNeo4j

        return RepositorioNeo4j(criar_driver(), obter_nome_banco())
    raise NotImplementedError(f"A integração com {modelo} ainda não está disponível.")
