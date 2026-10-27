from collections import Counter
from dataclasses import dataclass
from statistics import mean, median
from time import perf_counter

from bancos.neo4j.requisitos import codigos_requeridos
from consultas.normalizacao import normalizar_texto


@dataclass(frozen=True)
class Cenario:
    nome: str
    metodo: str
    argumentos: tuple


def cronometrar(funcao, *argumentos) -> tuple:
    inicio = perf_counter()
    resultado = funcao(*argumentos)
    return resultado, (perf_counter() - inicio) * 1000


def medir(funcao, *argumentos, repeticoes: int = 30, aquecimento: int = 3) -> dict:
    # O aquecimento absorve conexão e caches frios, que não representam o uso contínuo
    for _ in range(aquecimento):
        funcao(*argumentos)
    tempos = []
    resultado = []
    for _ in range(repeticoes):
        resultado, tempo = cronometrar(funcao, *argumentos)
        tempos.append(tempo)
    return {
        "mediana_ms": median(tempos),
        "media_ms": mean(tempos),
        "minimo_ms": min(tempos),
        "maximo_ms": max(tempos),
        "repeticoes": repeticoes,
        "resultados": len(resultado),
    }


def sugerir_parametros(componentes: list[dict]) -> dict:
    # Escolhe entradas a partir dos próprios dados para funcionar com qualquer curso
    if not componentes:
        return {"codigo": "", "termo": "", "periodo": 1, "alvo": ""}
    requeridos = {
        componente["codigo"]: set(codigos_requeridos(componente["pre_requisitos"]))
        for componente in componentes
    }
    mais_complexo = max(componentes, key=lambda componente: len(requeridos[componente["codigo"]]))
    vezes_requerido = Counter(codigo for codigos in requeridos.values() for codigo in codigos)
    internos = [codigo for codigo in vezes_requerido if codigo in requeridos]
    alvo = max(internos, key=lambda codigo: (vezes_requerido[codigo], codigo), default=mais_complexo["codigo"])
    palavras = normalizar_texto(mais_complexo["nome"]).split()
    termo = next((palavra for palavra in palavras if len(palavra) >= 4), " ".join(palavras))
    periodos = [componente["periodo"] for componente in componentes if componente["periodo"]]
    return {
        "codigo": mais_complexo["codigo"],
        "termo": termo,
        "periodo": min(periodos, default=1),
        "alvo": alvo,
    }


def montar_cenarios(estrutura_id: str, codigo: str, termo: str, periodo: int, alvo: str) -> list[Cenario]:
    return [
        Cenario("Estrutura completa", "listar_estrutura", (estrutura_id,)),
        Cenario("Busca por código", "buscar_por_codigo", (estrutura_id, codigo)),
        Cenario("Busca por nome", "buscar_por_nome", (estrutura_id, termo)),
        Cenario("Componentes do período", "listar_por_periodo", (estrutura_id, periodo)),
        Cenario("Dependentes diretos", "listar_dependentes", (estrutura_id, alvo)),
        Cenario("Cadeia de pré-requisitos", "listar_cadeia_pre_requisitos", (estrutura_id, codigo)),
    ]


def comparar(
    repositorios: dict,
    cenarios: list[Cenario],
    repeticoes: int = 30,
    aquecimento: int = 3,
) -> list[dict]:
    linhas = []
    for cenario in cenarios:
        for modelo, repositorio in repositorios.items():
            # Consultas exclusivas de um banco só são medidas onde existem
            funcao = getattr(repositorio, cenario.metodo, None)
            if funcao is None:
                continue
            linhas.append({
                "consulta": cenario.nome,
                "banco": modelo,
                **medir(funcao, *cenario.argumentos, repeticoes=repeticoes, aquecimento=aquecimento),
            })
    return linhas


def resultados_divergentes(linhas: list[dict]) -> list[str]:
    por_consulta = {}
    for linha in linhas:
        por_consulta.setdefault(linha["consulta"], set()).add(linha["resultados"])
    return [consulta for consulta, quantidades in por_consulta.items() if len(quantidades) > 1]
