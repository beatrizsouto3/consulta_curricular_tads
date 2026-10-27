import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "dados" / "curriculos" / "tads_ufrn_2019.json"


def requisito_valido(valor):
    if valor is None or valor == []:
        return True
    if not isinstance(valor, dict):
        return False
    if set(valor) == {"codigo"}:
        return isinstance(valor["codigo"], str) and bool(valor["codigo"])
    if set(valor) != {"operador", "termos"}:
        return False
    if valor["operador"] not in {"AND", "OR"}:
        return False
    termos = valor["termos"]
    return (
        isinstance(termos, list)
        and len(termos) >= 2
        and all(requisito_valido(termo) for termo in termos)
    )


def validar():
    dados = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    componentes = dados["componentes"]
    estrutura = dados["estrutura"]
    requisitos = dados["requisitos_integralizacao"]
    erros = []

    ids = [componente["componente_id"] for componente in componentes]
    codigos = [componente["codigo"] for componente in componentes]
    if len(ids) != len(set(ids)):
        erros.append("Há componente_id duplicado.")
    if len(codigos) != len(set(codigos)):
        erros.append("Há código duplicado nesta estrutura.")

    prefixo = estrutura["estrutura_id"] + ":"
    for componente in componentes:
        if componente["componente_id"] != prefixo + componente["codigo"]:
            erros.append(f"ID incompatível para {componente['codigo']}.")
        if componente["natureza"] == "obrigatorio":
            if componente["periodo"] not in range(1, estrutura["duracao_semestres"] + 1):
                erros.append(f"Período inválido para {componente['codigo']}.")
        elif componente["natureza"] == "optativo" and componente["periodo"] is not None:
            erros.append(f"Optativa com período fixado: {componente['codigo']}.")
        if not isinstance(componente["carga_horaria_horas"], int) or componente["carga_horaria_horas"] <= 0:
            erros.append(f"Carga horária inválida para {componente['codigo']}.")
        if not requisito_valido(componente["pre_requisitos"]):
            erros.append(f"Pré-requisitos inválidos para {componente['codigo']}.")

    total_requisitos = sum(item["carga_horaria_horas"] for item in requisitos)
    if total_requisitos != estrutura["carga_horaria_total_horas"]:
        erros.append("Os requisitos de integralização não somam a carga horária total.")

    horas_obrigatorias = sum(
        item["carga_horaria_horas"]
        for item in componentes
        if item["natureza"] == "obrigatorio"
    )
    horas_disciplinas_obrigatorias = sum(
        item["carga_horaria_horas"]
        for item in componentes
        if item["natureza"] == "obrigatorio" and item["tipo"] == "disciplina"
    )
    horas_integradoras = sum(
        item["carga_horaria_horas"]
        for item in componentes
        if item["tipo"] == "atividade_integradora"
    )
    horas_tcc = sum(
        item["carga_horaria_horas"]
        for item in componentes
        if item["tipo"] == "trabalho_conclusao"
    )
    horas_optativas_listadas = sum(
        item["carga_horaria_horas"]
        for item in componentes
        if item["natureza"] == "optativo"
    )

    if horas_obrigatorias != 1875:
        erros.append(f"Horas de componentes obrigatórios inesperadas: {horas_obrigatorias}.")
    if horas_disciplinas_obrigatorias != 1665:
        erros.append(f"Horas de disciplinas obrigatórias inesperadas: {horas_disciplinas_obrigatorias}.")
    if horas_integradoras != 120:
        erros.append(f"Horas de atividades integradoras inesperadas: {horas_integradoras}.")
    if horas_tcc != 90:
        erros.append(f"Horas de TCC inesperadas: {horas_tcc}.")
    if horas_optativas_listadas != 1155:
        erros.append(f"Horas do catálogo de optativas inesperadas: {horas_optativas_listadas}.")

    if erros:
        raise SystemExit("\n".join(erros))

    print(
        f"Currículo válido: {len(componentes)} componentes; "
        f"integralização {estrutura['carga_horaria_total_horas']}h; "
        f"catálogo optativo {horas_optativas_listadas}h."
    )


if __name__ == "__main__":
    validar()
