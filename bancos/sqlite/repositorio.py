import sqlite3
from collections import defaultdict

from bancos.sqlite.esquema import criar_esquema
from consultas.normalizacao import normalizar_texto


def _escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class RepositorioSQLite:
    CAMPOS_RESULTADO = (
        "componente_id",
        "codigo",
        "nome",
        "tipo",
        "natureza",
        "periodo",
        "carga_horaria_horas",
        "creditos",
        "pre_requisitos",
        "co_requisitos",
        "equivalencias",
    )

    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao
        self.conexao.row_factory = sqlite3.Row
        self.conexao.execute("PRAGMA foreign_keys = ON")
        # Permite abrir a interface antes da primeira importação
        criar_esquema(self.conexao)

    def fechar(self) -> None:
        self.conexao.close()

    def _filtrar_componentes(
        self,
        estrutura_id: str,
        condicao: str | None = None,
        parametros: tuple = (),
        natureza: str | None = None,
    ) -> list[dict]:
        condicoes = ["c.estrutura_id = ?"]
        valores = [estrutura_id]
        if condicao:
            condicoes.append(condicao)
            valores.extend(parametros)
        if natureza is not None:
            condicoes.append("a.natureza = ?")
            valores.append(natureza)

        linhas = self.conexao.execute(
            f"""
            SELECT c.componente_id, c.codigo, c.nome, c.tipo, a.natureza,
                   a.periodo, c.carga_horaria_horas, c.creditos,
                   c.equivalencias_conferido
            FROM componente c
            JOIN alocacao_curricular a
              ON a.estrutura_id = c.estrutura_id
             AND a.codigo = c.codigo
            WHERE {" AND ".join(condicoes)}
            ORDER BY (a.periodo IS NULL), a.periodo, c.codigo
            """,
            valores,
        ).fetchall()
        return self._montar_resultados(estrutura_id, linhas)

    def _carregar_arvores(
        self, estrutura_id: str, codigos: list[str]
    ) -> dict[tuple[str, str], object]:
        if not codigos:
            return {}
        marcadores = ",".join("?" for _ in codigos)
        arvores = self.conexao.execute(
            f"""
            SELECT arvore_id, componente_codigo, tipo, conferido
            FROM requisito_arvore
            WHERE estrutura_id = ?
              AND componente_codigo IN ({marcadores})
            """,
            (estrutura_id, *codigos),
        ).fetchall()
        if not arvores:
            return {}

        ids = tuple(arvore["arvore_id"] for arvore in arvores)
        marcadores_ids = ",".join("?" for _ in ids)
        nos = self.conexao.execute(
            f"""
            SELECT no_id, arvore_id, pai_id, ordem, operador, codigo
            FROM requisito_no
            WHERE arvore_id IN ({marcadores_ids})
            ORDER BY arvore_id, ordem
            """,
            ids,
        ).fetchall()

        raizes = {}
        filhos = defaultdict(list)
        for no in nos:
            if no["pai_id"] is None:
                raizes[no["arvore_id"]] = no
            else:
                filhos[(no["arvore_id"], no["pai_id"])].append(no)

        def montar(arvore_id: int, no) -> dict:
            if no["codigo"] is not None:
                return {"codigo": no["codigo"]}
            termos = sorted(
                filhos[(arvore_id, no["no_id"])], key=lambda item: item["ordem"]
            )
            return {
                "operador": no["operador"],
                "termos": [montar(arvore_id, termo) for termo in termos],
            }

        resultado = {}
        for arvore in arvores:
            raiz = raizes.get(arvore["arvore_id"])
            if raiz is None:
                valor = [] if arvore["conferido"] else None
            else:
                valor = montar(arvore["arvore_id"], raiz)
            resultado[(arvore["componente_codigo"], arvore["tipo"])] = valor
        return resultado

    def _carregar_equivalencias(
        self, estrutura_id: str, codigos: list[str]
    ) -> dict[str, list[str]]:
        if not codigos:
            return {}
        marcadores = ",".join("?" for _ in codigos)
        linhas = self.conexao.execute(
            f"""
            SELECT componente_codigo, codigo_equivalente
            FROM equivalencia
            WHERE estrutura_id = ?
              AND componente_codigo IN ({marcadores})
            ORDER BY componente_codigo, ordem
            """,
            (estrutura_id, *codigos),
        ).fetchall()
        equivalencias = defaultdict(list)
        for linha in linhas:
            equivalencias[linha["componente_codigo"]].append(
                linha["codigo_equivalente"]
            )
        return equivalencias

    def _montar_resultados(self, estrutura_id: str, linhas: list) -> list[dict]:
        if not linhas:
            return []
        codigos = list(dict.fromkeys(linha["codigo"] for linha in linhas))
        arvores = self._carregar_arvores(estrutura_id, codigos)
        equivalencias = self._carregar_equivalencias(estrutura_id, codigos)

        resultados = []
        for linha in linhas:
            codigo = linha["codigo"]
            if equivalencias.get(codigo):
                lista_equivalencias = equivalencias[codigo]
            elif linha["equivalencias_conferido"]:
                lista_equivalencias = []
            else:
                lista_equivalencias = None
            resultados.append(
                {
                    "componente_id": linha["componente_id"],
                    "codigo": codigo,
                    "nome": linha["nome"],
                    "tipo": linha["tipo"],
                    "natureza": linha["natureza"],
                    "periodo": linha["periodo"],
                    "carga_horaria_horas": linha["carga_horaria_horas"],
                    "creditos": linha["creditos"],
                    "pre_requisitos": arvores.get((codigo, "pre_requisito")),
                    "co_requisitos": arvores.get((codigo, "co_requisito")),
                    "equivalencias": lista_equivalencias,
                }
            )
        return resultados

    def buscar_por_codigo(
        self, estrutura_id: str, codigo: str, natureza: str | None = None
    ) -> list[dict]:
        codigo = codigo.strip().upper()
        if not codigo:
            return []
        return self._filtrar_componentes(
            estrutura_id, "c.codigo = ?", (codigo,), natureza
        )

    def buscar_por_nome(
        self, estrutura_id: str, termo: str, natureza: str | None = None
    ) -> list[dict]:
        termo_normalizado = normalizar_texto(termo)
        if not termo_normalizado:
            return []
        padrao = f"%{_escapar_like(termo_normalizado)}%"
        return self._filtrar_componentes(
            estrutura_id,
            "c.nome_busca LIKE ? ESCAPE '\\'",
            (padrao,),
            natureza,
        )

    def listar_por_periodo(
        self, estrutura_id: str, periodo: int, natureza: str | None = None
    ) -> list[dict]:
        if not isinstance(periodo, int) or periodo < 1:
            return []
        return self._filtrar_componentes(
            estrutura_id, "a.periodo = ?", (periodo,), natureza
        )

    def obter_prerequisitos(self, estrutura_id: str, codigo: str) -> list[dict]:
        return self.buscar_por_codigo(estrutura_id, codigo)

    def listar_estrutura(
        self, estrutura_id: str, natureza: str | None = None
    ) -> list[dict]:
        return self._filtrar_componentes(estrutura_id, natureza=natureza)

    def listar_estruturas(self) -> list[dict]:
        linhas = self.conexao.execute(
            """
            SELECT e.estrutura_id, c.nome AS curso, e.ano_inicio,
                   e.periodo_inicio, e.ativa
            FROM estrutura e
            JOIN curso c ON c.curso_id = e.curso_id
            ORDER BY e.estrutura_id
            """
        ).fetchall()
        return [
            {
                "estrutura_id": linha["estrutura_id"],
                "curso": linha["curso"],
                "ano_inicio": linha["ano_inicio"],
                "periodo_inicio": linha["periodo_inicio"],
                "ativa": bool(linha["ativa"]),
            }
            for linha in linhas
        ]

    def listar_dependentes(self, estrutura_id: str, codigo: str) -> list[dict]:
        codigo = codigo.strip().upper()
        if not codigo:
            return []
        return self._filtrar_componentes(
            estrutura_id,
            """
            EXISTS (
                SELECT 1
                FROM requisito_arvore arvore
                JOIN requisito_no no ON no.arvore_id = arvore.arvore_id
                WHERE arvore.estrutura_id = c.estrutura_id
                  AND arvore.componente_codigo = c.codigo
                  AND arvore.tipo = 'pre_requisito'
                  AND no.codigo = ?
            )
            """,
            (codigo,),
        )

    def listar_cadeia_pre_requisitos(
        self, estrutura_id: str, codigo: str
    ) -> list[dict]:
        codigo = codigo.strip().upper()
        if not codigo:
            return []
        linhas = self.conexao.execute(
            """
            WITH RECURSIVE cadeia(codigo, nivel) AS (
                SELECT no.codigo, 1
                FROM requisito_arvore arvore
                JOIN requisito_no no ON no.arvore_id = arvore.arvore_id
                WHERE arvore.estrutura_id = ?
                  AND arvore.componente_codigo = ?
                  AND arvore.tipo = 'pre_requisito'
                  AND no.codigo IS NOT NULL
                UNION
                SELECT no.codigo, anterior.nivel + 1
                FROM cadeia anterior
                JOIN requisito_arvore arvore
                  ON arvore.estrutura_id = ?
                 AND arvore.componente_codigo = anterior.codigo
                 AND arvore.tipo = 'pre_requisito'
                JOIN requisito_no no
                  ON no.arvore_id = arvore.arvore_id
                 AND no.codigo IS NOT NULL
                WHERE anterior.nivel < 50
            ),
            resumo AS (
                SELECT codigo, MIN(nivel) AS nivel
                FROM cadeia
                GROUP BY codigo
            )
            SELECT resumo.codigo, componente.nome, alocacao.periodo,
                   (componente.codigo IS NULL) AS externo, resumo.nivel
            FROM resumo
            LEFT JOIN componente
              ON componente.estrutura_id = ?
             AND componente.codigo = resumo.codigo
            LEFT JOIN alocacao_curricular alocacao
              ON alocacao.estrutura_id = componente.estrutura_id
             AND alocacao.codigo = componente.codigo
            ORDER BY resumo.nivel, resumo.codigo
            """,
            (estrutura_id, codigo, estrutura_id, estrutura_id),
        ).fetchall()
        return [
            {
                "codigo": linha["codigo"],
                "nome": linha["nome"],
                "periodo": linha["periodo"],
                "externo": bool(linha["externo"]),
                "nivel": linha["nivel"],
            }
            for linha in linhas
        ]
