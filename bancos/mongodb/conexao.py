import os

from dotenv import load_dotenv
from pymongo import MongoClient


def criar_cliente() -> MongoClient:
    load_dotenv()
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    return MongoClient(uri, serverSelectionTimeoutMS=3000)


def obter_banco(cliente: MongoClient):
    load_dotenv()
    nome = os.getenv("MONGODB_DATABASE", "consulta_curricular_tads")
    return cliente[nome]


def testar_conexao() -> None:
    cliente = criar_cliente()
    try:
        cliente.admin.command("ping")
    finally:
        cliente.close()
