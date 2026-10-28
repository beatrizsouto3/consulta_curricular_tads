import sqlite3

from bancos.sqlite.esquema import criar_esquema
from consultas.normalizacao import normalizar_texto


def _normalizar_expressao(valor):
    # A lista canônica representa requisitos independentes: tratamos como AND
    if isinstance(valor, list):
        return {
            "operador": "AND",
            "termos": [
                {"codigo": item} if isinstance(item, str) else _normalizar_expressao(item)
                for item in valor
            ],
        }
    if isinstance(valor, str):
        return {"codigo": valor}
    return valor


def _gravar_no(
    conexao: sqlite3.Connection,
    arvore_id: int,
    pai_id: int | None,
    ordem: int | None,
    no: dict,
) -> None:
    if isinstance(no, str):
        no = {"codigo": no}
    if "codigo" in no:
        conexao.execute(
            """
            INSERT INTO requisito_no (arvore_id, pai_id, ordem, operador, codigo)
            VALUES (?, ?, ?, NULL, ?)
            """,
            (arvore_id, pai_id, ordem, no["codigo"]),
        )
        return

    operador = no.get("operador")
    if operador not in {"AND", "OR"}:
        raise ValueError(f"Operador de requisito inválido: {operador!r}.")
    cursor = conexao.execute(
        """
        INSERT INTO requisito_no (arvore_id, pai_id, ordem, operador, codigo)
        VALUES (?, ?, ?, ?, NULL)
        """,
        (arvore_id, pai_id, ordem, operador),
    )
    for posicao, termo in enumerate(no.get("termos", [])):
        _gravar_no(conexao, arvore_id, cursor.lastrowid, posicao, termo)


def _gravar_arvore(
    conexao: sqlite3.Connection,
    estrutura_id: str,
    componente_codigo: str,
    tipo: str,
    requisito,
) -> None:
    conferido = 0 if requisito is None else 1
    cursor = conexao.execute(
        """
        INSERT INTO requisito_arvore
            (estrutura_id, componente_codigo, tipo, conferido)
        VALUES (?, ?, ?, ?)
        """,
        (estrutura_id, componente_codigo, tipo, conferido),
    )
    arvore_id = cursor.lastrowid

    if requisito is None or requisito == []:
        return
    _gravar_no(conexao, arvore_id, None, None, _normalizar_expressao(requisito))


def importar_curriculo(conexao: sqlite3.Connection, curriculo: dict) -> dict:
    criar_esquema(conexao)
    # Garante o cascade mesmo se a conexão tiver sido aberta fora de conexao.py
    conexao.execute("PRAGMA foreign_keys = ON")

    curso = curriculo["curso"]
    estrutura = curriculo["estrutura"]
    estrutura_id = estrutura["estrutura_id"]
    componentes = curriculo["componentes"]

    with conexao:
        # A remoção em cascata limpa componentes, alocações, árvores e requisitos
        conexao.execute(
            "DELETE FROM estrutura WHERE estrutura_id = ?", (estrutura_id,)
        )
        conexao.execute(
            """
            INSERT INTO curso
                (curso_id, nome, instituicao, unidade, municipio, modalidade, grau)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (curso_id) DO UPDATE SET
                nome = excluded.nome,
                instituicao = excluded.instituicao,
                unidade = excluded.unidade,
                municipio = excluded.municipio,
                modalidade = excluded.modalidade,
                grau = excluded.grau
            """,
            (
                curso["curso_id"],
                curso["nome"],
                curso["instituicao"],
                curso["unidade"],
                curso["municipio"],
                curso["modalidade"],
                curso["grau"],
            ),
        )
        conexao.execute(
            """
            INSERT INTO estrutura
                (estrutura_id, curso_id, schema_version, codigo_sigaa,
                 ano_inicio, periodo_inicio, ativa, duracao_semestres,
                 carga_horaria_total_horas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                estrutura_id,
                estrutura["curso_id"],
                curriculo["schema_version"],
                estrutura["codigo_sigaa"],
                estrutura["ano_inicio"],
                estrutura["periodo_inicio"],
                int(bool(estrutura["ativa"])),
                estrutura["duracao_semestres"],
                estrutura["carga_horaria_total_horas"],
            ),
        )

        for ordem, turno in enumerate(estrutura.get("turnos", [])):
            conexao.execute(
                """
                INSERT INTO estrutura_turno (estrutura_id, ordem, turno)
                VALUES (?, ?, ?)
                """,
                (estrutura_id, ordem, turno),
            )

        for ordem, fonte in enumerate(estrutura.get("fontes", [])):
            conexao.execute(
                """
                INSERT INTO estrutura_fonte
                    (estrutura_id, ordem, url, coletada_em, escopo)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    estrutura_id,
                    ordem,
                    fonte["url"],
                    fonte.get("coletada_em"),
                    fonte.get("escopo"),
                ),
            )

        for ordem, requisito in enumerate(
            curriculo.get("requisitos_integralizacao", [])
        ):
            conexao.execute(
                """
                INSERT INTO requisito_integralizacao
                    (estrutura_id, ordem, categoria, carga_horaria_horas)
                VALUES (?, ?, ?, ?)
                """,
                (
                    estrutura_id,
                    ordem,
                    requisito["categoria"],
                    requisito["carga_horaria_horas"],
                ),
            )

        for componente in componentes:
            codigo = componente["codigo"]
            equivalencias = componente.get("equivalencias")
            conexao.execute(
                """
                INSERT INTO componente
                    (estrutura_id, codigo, componente_id, nome, nome_busca,
                     tipo, carga_horaria_horas, creditos, modalidade,
                     equivalencias_conferido)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    estrutura_id,
                    codigo,
                    componente.get("componente_id") or f"{estrutura_id}:{codigo}",
                    componente["nome"],
                    normalizar_texto(componente["nome"]),
                    componente["tipo"],
                    componente.get("carga_horaria_horas"),
                    componente.get("creditos"),
                    componente.get("modalidade"),
                    int(equivalencias is not None),
                ),
            )
            conexao.execute(
                """
                INSERT INTO alocacao_curricular
                    (estrutura_id, codigo, periodo, natureza)
                VALUES (?, ?, ?, ?)
                """,
                (
                    estrutura_id,
                    codigo,
                    componente.get("periodo"),
                    componente["natureza"],
                ),
            )
            for ordem, codigo_equivalente in enumerate(equivalencias or []):
                conexao.execute(
                    """
                    INSERT INTO equivalencia
                        (estrutura_id, componente_codigo, ordem, codigo_equivalente)
                    VALUES (?, ?, ?, ?)
                    """,
                    (estrutura_id, codigo, ordem, codigo_equivalente),
                )

            _gravar_arvore(
                conexao,
                estrutura_id,
                codigo,
                "pre_requisito",
                componente.get("pre_requisitos"),
            )
            _gravar_arvore(
                conexao,
                estrutura_id,
                codigo,
                "co_requisito",
                componente.get("co_requisitos"),
            )

    return {
        "estrutura_id": estrutura_id,
        "componentes": len(componentes),
        "requisitos_integralizacao": len(
            curriculo.get("requisitos_integralizacao", [])
        ),
    }
