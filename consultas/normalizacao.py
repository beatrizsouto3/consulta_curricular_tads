import unicodedata


def normalizar_texto(texto: str) -> str:
    sem_acentos = unicodedata.normalize("NFD", texto.casefold())
    simples = "".join(
        caractere
        for caractere in sem_acentos
        if unicodedata.category(caractere) != "Mn"
    )
    return " ".join(simples.split())
