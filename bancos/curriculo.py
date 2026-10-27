import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PASTA_CURRICULOS = ROOT / "dados" / "curriculos"
CURRICULO_PADRAO = PASTA_CURRICULOS / "tads_ufrn_2019.json"


def carregar_curriculo(caminho: Path = CURRICULO_PADRAO) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def listar_curriculos(pasta: Path = PASTA_CURRICULOS) -> list[Path]:
    return sorted(pasta.glob("*.json"))
