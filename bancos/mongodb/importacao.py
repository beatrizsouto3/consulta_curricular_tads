import json
from pathlib import Path

from consultas.normalizacao import normalizar_texto


ROOT = Path(__file__).resolve().parents[2]
CURRICULO_PADRAO = ROOT / "dados" / "curriculos" / "tads_ufrn_2019.json"


def carregar_curriculo(caminho: Path = CURRICULO_PADRAO) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


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
