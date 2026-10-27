import os

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase


def criar_driver() -> Driver:
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    usuario = os.getenv("NEO4J_USER", "neo4j")
    senha = os.getenv("NEO4J_PASSWORD", "consulta_tads")
    return GraphDatabase.driver(uri, auth=(usuario, senha), connection_timeout=3)


def obter_nome_banco() -> str:
    load_dotenv()
    return os.getenv("NEO4J_DATABASE", "neo4j")


def testar_conexao() -> None:
    driver = criar_driver()
    try:
        driver.verify_connectivity()
    finally:
        driver.close()
