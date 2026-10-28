import argparse
import csv
import sys
from pathlib import Path

from consultas.desempenho import comparar, montar_cenarios, resultados_divergentes, sugerir_parametros
from consultas.fabrica import MODELOS, criar_repositorio


COLUNAS = ("consulta", "banco", "mediana_ms", "media_ms", "minimo_ms", "maximo_ms", "repeticoes", "resultados")


def _ler_argumentos(argumentos: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compara o tempo de resposta das consultas em cada banco.")
    parser.add_argument("--bancos", nargs="+", choices=MODELOS, default=list(MODELOS))
    parser.add_argument("--estrutura", help="estrutura_id; por padrão, a primeira disponível")
    parser.add_argument("--repeticoes", type=int, default=30)
    parser.add_argument("--aquecimento", type=int, default=3)
    parser.add_argument("--saida", type=Path, help="caminho do CSV com os resultados")
    return parser.parse_args(argumentos)


def _abrir_repositorios(modelos: list[str]) -> dict:
    repositorios = {}
    for modelo in modelos:
        repositorio = None
        try:
            repositorio = criar_repositorio(modelo)
            repositorio.listar_estruturas()
        except NotImplementedError:
            print(f"{modelo}: integração ainda não disponível, ignorado.")
        except Exception as erro:
            print(f"{modelo}: indisponível ({erro.__class__.__name__}), ignorado.")
            if repositorio is not None:
                repositorio.fechar()
        else:
            repositorios[modelo] = repositorio
    return repositorios


def _imprimir(linhas: list[dict]) -> None:
    print(f"\n{'Consulta':<26} {'Banco':<8} {'Mediana':>10} {'Mínimo':>10} {'Máximo':>10} {'Itens':>6}")
    for linha in linhas:
        print(
            f"{linha['consulta']:<26} {linha['banco']:<8} "
            f"{linha['mediana_ms']:>8.3f}ms {linha['minimo_ms']:>8.3f}ms "
            f"{linha['maximo_ms']:>8.3f}ms {linha['resultados']:>6}"
        )


def main(argumentos: list[str]) -> int:
    opcoes = _ler_argumentos(argumentos)
    repositorios = _abrir_repositorios(opcoes.bancos)
    if not repositorios:
        print("Nenhum banco disponível para comparar.")
        return 1

    try:
        referencia = next(iter(repositorios.values()))
        estrutura_id = opcoes.estrutura or referencia.listar_estruturas()[0]["estrutura_id"]
        parametros = sugerir_parametros(referencia.listar_estrutura(estrutura_id))
        print(f"Estrutura {estrutura_id}; parâmetros: {parametros}.")
        print(f"{opcoes.aquecimento} execuções de aquecimento e {opcoes.repeticoes} medidas por consulta.")
        linhas = comparar(
            repositorios,
            montar_cenarios(estrutura_id, **parametros),
            opcoes.repeticoes,
            opcoes.aquecimento,
        )
    finally:
        for repositorio in repositorios.values():
            repositorio.fechar()

    _imprimir(linhas)
    for consulta in resultados_divergentes(linhas):
        print(f"Atenção: os bancos devolveram quantidades diferentes em '{consulta}'.")
    if opcoes.saida:
        opcoes.saida.parent.mkdir(parents=True, exist_ok=True)
        with opcoes.saida.open("w", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS)
            escritor.writeheader()
            escritor.writerows(linhas)
        print(f"\nResultados gravados em {opcoes.saida}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
