from collections import defaultdict
from itertools import count


def codigos_requeridos(requisito) -> list[str]:
    if isinstance(requisito, dict) and "codigo" in requisito:
        return [requisito["codigo"]]
    if isinstance(requisito, dict):
        return [codigo for termo in requisito["termos"] for codigo in codigos_requeridos(termo)]
    if isinstance(requisito, list):
        return [codigo for termo in requisito for codigo in codigos_requeridos(termo)]
    return []


def achatar_requisito(estrutura_id: str, componente_id: str, requisito) -> dict:
    # Converte a árvore AND/OR em grupos e arestas ordenadas
    grafo = {"grupos": [], "exige": [], "termos": []}
    if not requisito:
        return grafo
    if isinstance(requisito, list):
        raise ValueError(f"Lista de requisitos não suportada em {componente_id}.")
    sequencia = count(1)

    def registrar(no) -> tuple[str, bool]:
        if "codigo" in no:
            return f"{estrutura_id}:{no['codigo']}", False
        grupo_id = f"{componente_id}#{next(sequencia)}"
        grafo["grupos"].append(
            {"grupo_id": grupo_id, "estrutura_id": estrutura_id, "operador": no["operador"]}
        )
        for ordem, termo in enumerate(no["termos"]):
            destino, destino_grupo = registrar(termo)
            grafo["termos"].append(
                {"grupo_id": grupo_id, "ordem": ordem, "destino": destino, "destino_grupo": destino_grupo}
            )
        return grupo_id, True

    destino, destino_grupo = registrar(requisito)
    grafo["exige"].append({"origem": componente_id, "destino": destino, "destino_grupo": destino_grupo})
    return grafo


def montar_requisito(raiz_grupo, raiz_codigo, arestas: list[dict], conferido: bool):
    if raiz_grupo is None and raiz_codigo is None:
        return [] if conferido else None
    operadores = {}
    filhos = defaultdict(list)
    for aresta in arestas:
        operadores[aresta["grupo"]] = aresta["operador"]
        filhos[aresta["grupo"]].append(aresta)

    def montar(grupo_id, codigo):
        if grupo_id is None:
            return {"codigo": codigo}
        termos = sorted(filhos[grupo_id], key=lambda aresta: aresta["ordem"])
        return {
            "operador": operadores[grupo_id],
            "termos": [montar(termo["filho_grupo"], termo["filho_codigo"]) for termo in termos],
        }

    return montar(raiz_grupo, raiz_codigo)
