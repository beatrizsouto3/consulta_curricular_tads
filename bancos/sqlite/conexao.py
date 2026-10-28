import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[2]
CAMINHO_PADRAO = ROOT / "dados" / "consulta_curricular.sqlite3"


def obter_caminho() -> Path:
    load_dotenv()
    valor = os.getenv("SQLITE_PATH", str(CAMINHO_PADRAO))
    caminho = Path(valor).expanduser()
    if not caminho.is_absolute():
        caminho = ROOT / caminho
    return caminho


def criar_conexao(caminho: str | Path | None = None) -> sqlite3.Connection:
    if caminho is None:
        caminho = obter_caminho()
    if str(caminho) != ":memory:":
        caminho = Path(caminho)
        caminho.parent.mkdir(parents=True, exist_ok=True)
    # O Streamlit reaproveita o repositório entre execuções da interface
    conexao = sqlite3.connect(
        str(caminho),
        timeout=5,
        check_same_thread=False,
    )
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def testar_conexao(caminho: str | Path | None = None) -> None:
    conexao = criar_conexao(caminho)
    try:
        conexao.execute("SELECT 1").fetchone()
    finally:
        conexao.close()
