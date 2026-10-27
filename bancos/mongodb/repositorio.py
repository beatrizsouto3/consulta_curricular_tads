import re

from consultas.normalizacao import normalizar_texto


class RepositorioMongoDB:
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

    def __init__(self, banco):
        self.colecao = banco["estruturas_curriculares"]

    def fechar(self) -> None:
        self.colecao.database.client.close()

    def _filtrar_componentes(
        self,
        estrutura_id: str,
        condicao: dict,
        filtro: dict,
        natureza: str | None = None,
    ) -> list[dict]:
        if natureza is not None:
            condicao = {
                "$and": [condicao, {"$eq": ["$$componente.natureza", natureza]}]
            }
            filtro = {**filtro, "componentes.natureza": natureza}
        pipeline = [
            {"$match": {"_id": estrutura_id, **filtro}},
            {
                "$project": {
                    "_id": 0,
                    "componentes": {
                        "$filter": {
                            "input": "$componentes",
                            "as": "componente",
                            "cond": condicao,
                        }
                    },
                }
            },
        ]
        resultado = next(iter(self.colecao.aggregate(pipeline)), None)
        if resultado is None:
            return []
        return self._normalizar_resultados(resultado["componentes"])

    def _normalizar_resultados(self, componentes: list[dict]) -> list[dict]:
        resultados = [
            {campo: componente.get(campo) for campo in self.CAMPOS_RESULTADO}
            for componente in componentes
        ]
        return sorted(
            resultados,
            key=lambda item: (
                item["periodo"] is None,
                item["periodo"] or 0,
                item["codigo"],
            ),
        )

    def buscar_por_codigo(
        self, estrutura_id: str, codigo: str, natureza: str | None = None
    ) -> list[dict]:
        codigo = codigo.strip().upper()
        if not codigo:
            return []
        return self._filtrar_componentes(
            estrutura_id,
            {"$eq": ["$$componente.codigo", codigo]},
            {"componentes.codigo": codigo},
            natureza,
        )

    def buscar_por_nome(
        self, estrutura_id: str, termo: str, natureza: str | None = None
    ) -> list[dict]:
        termo_normalizado = normalizar_texto(termo)
        if not termo_normalizado:
            return []
        padrao = re.escape(termo_normalizado)
        return self._filtrar_componentes(
            estrutura_id,
            {
                "$regexMatch": {
                    "input": "$$componente.nome_busca",
                    "regex": {"$literal": padrao},
                }
            },
            {"componentes.nome_busca": {"$regex": padrao}},
            natureza,
        )

    def listar_por_periodo(
        self, estrutura_id: str, periodo: int, natureza: str | None = None
    ) -> list[dict]:
        if not isinstance(periodo, int) or periodo < 1:
            return []
        return self._filtrar_componentes(
            estrutura_id,
            {"$eq": ["$$componente.periodo", periodo]},
            {"componentes.periodo": periodo},
            natureza,
        )

    def obter_prerequisitos(self, estrutura_id: str, codigo: str) -> list[dict]:
        return self.buscar_por_codigo(estrutura_id, codigo)

    def listar_estrutura(
        self, estrutura_id: str, natureza: str | None = None
    ) -> list[dict]:
        documento = self.colecao.find_one(
            {"_id": estrutura_id},
            {"_id": 0, "componentes": 1},
        )
        if documento is None:
            return []
        componentes = documento["componentes"]
        if natureza is not None:
            componentes = [item for item in componentes if item.get("natureza") == natureza]
        return self._normalizar_resultados(componentes)

    def listar_estruturas(self) -> list[dict]:
        documentos = self.colecao.find(
            {},
            {"_id": 1, "curso.nome": 1, "estrutura.ano_inicio": 1,
             "estrutura.periodo_inicio": 1, "estrutura.ativa": 1},
        )
        return [
            {
                "estrutura_id": documento["_id"],
                "curso": documento.get("curso", {}).get("nome", ""),
                "ano_inicio": documento.get("estrutura", {}).get("ano_inicio"),
                "periodo_inicio": documento.get("estrutura", {}).get("periodo_inicio"),
                "ativa": documento.get("estrutura", {}).get("ativa", False),
            }
            for documento in documentos
        ]

    def listar_dependentes(self, estrutura_id: str, codigo: str) -> list[dict]:
        codigo = codigo.strip().upper()
        if not codigo:
            return []
        componentes = self.listar_estrutura(estrutura_id)
        return [
            componente
            for componente in componentes
            if self._possui_pre_requisito(componente["pre_requisitos"], codigo)
        ]

    @classmethod
    def _possui_pre_requisito(cls, requisito, codigo: str) -> bool:
        if isinstance(requisito, dict):
            if requisito.get("codigo", "").upper() == codigo:
                return True
            return any(
                cls._possui_pre_requisito(termo, codigo)
                for termo in requisito.get("termos", [])
            )
        if isinstance(requisito, list):
            return any(cls._possui_pre_requisito(termo, codigo) for termo in requisito)
        return False
