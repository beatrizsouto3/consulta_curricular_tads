import json

from bancos.neo4j.requisitos import achatar_requisito, codigos_requeridos
from consultas.normalizacao import normalizar_texto


ESQUEMA = (
    "CREATE CONSTRAINT curso_id IF NOT EXISTS FOR (n:Curso) REQUIRE n.curso_id IS UNIQUE",
    "CREATE CONSTRAINT estrutura_id IF NOT EXISTS FOR (n:Estrutura) REQUIRE n.estrutura_id IS UNIQUE",
    "CREATE CONSTRAINT componente_id IF NOT EXISTS FOR (n:Componente) REQUIRE n.componente_id IS UNIQUE",
    "CREATE CONSTRAINT grupo_requisito_id IF NOT EXISTS FOR (n:GrupoRequisito) REQUIRE n.grupo_id IS UNIQUE",
    "CREATE INDEX componente_estrutura IF NOT EXISTS FOR (n:Componente) ON (n.estrutura_id)",
    "CREATE INDEX grupo_requisito_estrutura IF NOT EXISTS FOR (n:GrupoRequisito) ON (n.estrutura_id)",
    "CREATE INDEX integralizacao_estrutura IF NOT EXISTS FOR (n:RequisitoIntegralizacao) ON (n.estrutura_id)",
)

REMOCOES = (
    "MATCH (n:Componente {estrutura_id: $estrutura_id}) DETACH DELETE n",
    "MATCH (n:GrupoRequisito {estrutura_id: $estrutura_id}) DETACH DELETE n",
    "MATCH (n:RequisitoIntegralizacao {estrutura_id: $estrutura_id}) DETACH DELETE n",
    "MATCH (n:Estrutura {estrutura_id: $estrutura_id}) DETACH DELETE n",
)

GRAVAR_ESTRUTURA = """
MERGE (curso:Curso {curso_id: $curso.curso_id})
SET curso += $curso
CREATE (estrutura:Estrutura)
SET estrutura = $estrutura
CREATE (curso)-[:POSSUI_ESTRUTURA]->(estrutura)
WITH estrutura
UNWIND $integralizacao AS requisito
CREATE (estrutura)-[:EXIGE_INTEGRALIZACAO]->(item:RequisitoIntegralizacao)
SET item = requisito, item.estrutura_id = $estrutura.estrutura_id
"""

GRAVAR_COMPONENTES = """
MATCH (estrutura:Estrutura {estrutura_id: $estrutura_id})
UNWIND $componentes AS propriedades
CREATE (estrutura)-[:CONTEM]->(componente:Componente)
SET componente = propriedades
"""

GRAVAR_EXTERNOS = """
UNWIND $externos AS propriedades
CREATE (componente:Componente)
SET componente = propriedades
"""

GRAVAR_GRUPOS = """
UNWIND $grupos AS propriedades
CREATE (grupo:GrupoRequisito)
SET grupo = propriedades
"""

GRAVAR_ARESTAS = {
    ("exige", False): """
        UNWIND $arestas AS aresta
        MATCH (origem:Componente {componente_id: aresta.origem})
        MATCH (destino:Componente {componente_id: aresta.destino})
        CREATE (origem)-[:EXIGE]->(destino)
    """,
    ("exige", True): """
        UNWIND $arestas AS aresta
        MATCH (origem:Componente {componente_id: aresta.origem})
        MATCH (destino:GrupoRequisito {grupo_id: aresta.destino})
        CREATE (origem)-[:EXIGE]->(destino)
    """,
    ("termos", False): """
        UNWIND $arestas AS aresta
        MATCH (grupo:GrupoRequisito {grupo_id: aresta.grupo_id})
        MATCH (destino:Componente {componente_id: aresta.destino})
        CREATE (grupo)-[:TERMO {ordem: aresta.ordem}]->(destino)
    """,
    ("termos", True): """
        UNWIND $arestas AS aresta
        MATCH (grupo:GrupoRequisito {grupo_id: aresta.grupo_id})
        MATCH (destino:GrupoRequisito {grupo_id: aresta.destino})
        CREATE (grupo)-[:TERMO {ordem: aresta.ordem}]->(destino)
    """,
}

GRAVAR_DEPENDENCIAS = """
UNWIND $arestas AS aresta
MATCH (origem:Componente {componente_id: aresta.origem})
MATCH (destino:Componente {componente_id: aresta.destino})
MERGE (origem)-[:DEPENDE_DE]->(destino)
"""


def _propriedades_componente(componente: dict, estrutura_id: str) -> dict:
    campos = (
        "componente_id", "codigo", "nome", "tipo", "natureza", "periodo",
        "carga_horaria_horas", "creditos", "modalidade", "equivalencias",
    )
    return {
        **{campo: componente.get(campo) for campo in campos},
        "estrutura_id": estrutura_id,
        "nome_busca": normalizar_texto(componente["nome"]),
        "externo": False,
        "pre_requisitos_conferido": componente.get("pre_requisitos") is not None,
        # Co-requisitos podem ser árvores; ficam serializados por não serem consultados
        "co_requisitos_json": json.dumps(componente.get("co_requisitos"), ensure_ascii=False),
    }


def montar_grafo(curriculo: dict) -> dict:
    estrutura = curriculo["estrutura"]
    estrutura_id = estrutura["estrutura_id"]
    componentes = curriculo["componentes"]
    codigos = {componente["codigo"] for componente in componentes}

    grafo = {
        "estrutura": {
            **{campo: valor for campo, valor in estrutura.items() if campo != "fontes"},
            "schema_version": curriculo["schema_version"],
            "fontes_json": json.dumps(estrutura.get("fontes", []), ensure_ascii=False),
        },
        "componentes": [_propriedades_componente(componente, estrutura_id) for componente in componentes],
        "externos": [],
        "grupos": [],
        "exige": [],
        "termos": [],
        "depende_de": [],
    }
    externos = set()
    for componente in componentes:
        requisito = componente.get("pre_requisitos")
        parcial = achatar_requisito(estrutura_id, componente["componente_id"], requisito)
        for chave in ("grupos", "exige", "termos"):
            grafo[chave].extend(parcial[chave])
        for codigo in dict.fromkeys(codigos_requeridos(requisito)):
            grafo["depende_de"].append(
                {"origem": componente["componente_id"], "destino": f"{estrutura_id}:{codigo}"}
            )
            if codigo not in codigos:
                externos.add(codigo)

    # Códigos de currículos anteriores viram nós sem vínculo CONTEM com a estrutura
    grafo["externos"] = [
        {
            "componente_id": f"{estrutura_id}:{codigo}",
            "estrutura_id": estrutura_id,
            "codigo": codigo,
            "externo": True,
        }
        for codigo in sorted(externos)
    ]
    return grafo


def _gravar(tx, curriculo: dict, grafo: dict) -> None:
    estrutura_id = grafo["estrutura"]["estrutura_id"]
    for consulta in REMOCOES:
        tx.run(consulta, estrutura_id=estrutura_id)
    tx.run(
        GRAVAR_ESTRUTURA,
        curso=curriculo["curso"],
        estrutura=grafo["estrutura"],
        integralizacao=curriculo.get("requisitos_integralizacao", []),
    )
    tx.run(GRAVAR_COMPONENTES, estrutura_id=estrutura_id, componentes=grafo["componentes"])
    tx.run(GRAVAR_EXTERNOS, externos=grafo["externos"])
    tx.run(GRAVAR_GRUPOS, grupos=grafo["grupos"])
    for (chave, destino_grupo), consulta in GRAVAR_ARESTAS.items():
        arestas = [aresta for aresta in grafo[chave] if aresta["destino_grupo"] == destino_grupo]
        tx.run(consulta, arestas=arestas)
    tx.run(GRAVAR_DEPENDENCIAS, arestas=grafo["depende_de"])


def importar_curriculo(driver, curriculo: dict, banco: str | None = None) -> dict:
    grafo = montar_grafo(curriculo)
    with driver.session(database=banco) as sessao:
        # Restrições de esquema não podem dividir a transação com escritas de dados
        for consulta in ESQUEMA:
            sessao.run(consulta).consume()
        sessao.execute_write(_gravar, curriculo, grafo)
    return {
        "estrutura_id": grafo["estrutura"]["estrutura_id"],
        "componentes": len(grafo["componentes"]),
        "externos": len(grafo["externos"]),
        "grupos": len(grafo["grupos"]),
        "dependencias": len(grafo["depende_de"]),
    }
