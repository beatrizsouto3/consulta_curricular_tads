from bancos.curriculo import CURRICULO_PADRAO, carregar_curriculo
from consultas.normalizacao import normalizar_texto


def montar_documento(curriculo: dict) -> dict:
    estrutura = curriculo["estrutura"]
    componentes = [
        {**componente, "nome_busca": normalizar_texto(componente["nome"])}
        for componente in curriculo["componentes"]
    ]
    return {
        "_id": estrutura["estrutura_id"],
        "schema_version": curriculo["schema_version"],
        "curso": curriculo["curso"],
        "estrutura": estrutura,
        "requisitos_integralizacao": curriculo["requisitos_integralizacao"],
        "componentes": componentes,
    }


def importar_curriculo(banco, curriculo: dict):
    colecao = banco["estruturas_curriculares"]
    colecao.create_index("componentes.codigo")
    colecao.create_index("componentes.periodo")

    documento = montar_documento(curriculo)
    return colecao.replace_one(
        {"_id": documento["_id"]},
        documento,
        upsert=True,
    )
