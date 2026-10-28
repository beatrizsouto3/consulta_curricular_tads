from pathlib import Path

ARQUIVO_ESQUEMA = Path(__file__).with_name("esquema.sql")


def criar_esquema(conexao) -> None:
    conexao.executescript(ARQUIVO_ESQUEMA.read_text(encoding="utf-8"))
