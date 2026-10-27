import json

from neo4j import RoutingControl

from bancos.neo4j.requisitos import montar_requisito
from consultas.normalizacao import normalizar_texto


CONSULTA_COMPONENTES = """
MATCH (:Estrutura {estrutura_id: $estrutura_id})-[:CONTEM]->(c:Componente)
WHERE (%s) AND ($natureza IS NULL OR c.natureza = $natureza)
OPTIONAL MATCH (c)-[:EXIGE]->(raiz)
OPTIONAL MATCH (raiz)-[:TERMO*0..]->(g:GrupoRequisito)-[t:TERMO]->(filho)
WITH c, raiz, collect(CASE WHEN g IS NULL THEN null ELSE {
    grupo: g.grupo_id, operador: g.operador, ordem: t.ordem,
    filho_grupo: filho.grupo_id, filho_codigo: filho.codigo
} END) AS arestas
RETURN c {.*} AS componente, raiz.grupo_id AS raiz_grupo, raiz.codigo AS raiz_codigo, arestas
ORDER BY c.periodo IS NULL, coalesce(c.periodo, 0), c.codigo
"""

CONSULTA_ESTRUTURAS = """
MATCH (curso:Curso)-[:POSSUI_ESTRUTURA]->(e:Estrutura)
RETURN e.estrutura_id AS estrutura_id, curso.nome AS curso, e.ano_inicio AS ano_inicio,
       e.periodo_inicio AS periodo_inicio, coalesce(e.ativa, false) AS ativa
ORDER BY e.estrutura_id
"""

CONSULTA_CADEIA = """
MATCH (:Estrutura {estrutura_id: $estrutura_id})-[:CONTEM]->(c:Componente {codigo: $codigo})
MATCH caminho = (c)-[:DEPENDE_DE*1..]->(requisito:Componente)
WITH requisito, min(length(caminho)) AS nivel
RETURN requisito.codigo AS codigo, requisito.nome AS nome, requisito.periodo AS periodo,
       requisito.externo AS externo, nivel
ORDER BY nivel, codigo
"""


class RepositorioNeo4j:
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

    def __init__(self, driver, banco: str | None = None):
        self.driver = driver
        self.banco = banco

    def fechar(self) -> None:
        self.driver.close()

    def _executar(self, consulta: str, **parametros) -> list:
        registros, _, _ = self.driver.execute_query(
            consulta, parametros, database_=self.banco, routing_=RoutingControl.READ
        )
        return registros

    def _filtrar_componentes(
        self,
        estrutura_id: str,
        condicao: str,
        natureza: str | None = None,
        **parametros,
    ) -> list[dict]:
        registros = self._executar(
            CONSULTA_COMPONENTES % condicao,
            estrutura_id=estrutura_id,
            natureza=natureza,
            **parametros,
        )
        return [self._normalizar_resultado(registro) for registro in registros]

    def _normalizar_resultado(self, registro) -> dict:
        componente = registro["componente"]
        resultado = {campo: componente.get(campo) for campo in self.CAMPOS_RESULTADO}
        resultado["pre_requisitos"] = montar_requisito(
            registro["raiz_grupo"],
            registro["raiz_codigo"],
            registro["arestas"],
            componente.get("pre_requisitos_conferido", False),
        )
        resultado["co_requisitos"] = json.loads(componente.get("co_requisitos_json") or "null")
        return resultado

    def buscar_por_codigo(
        self, estrutura_id: str, codigo: str, natureza: str | None = None
    ) -> list[dict]:
        codigo = codigo.strip().upper()
        if not codigo:
            return []
        return self._filtrar_componentes(estrutura_id, "c.codigo = $codigo", natureza, codigo=codigo)

    def buscar_por_nome(
        self, estrutura_id: str, termo: str, natureza: str | None = None
    ) -> list[dict]:
        termo_normalizado = normalizar_texto(termo)
        if not termo_normalizado:
            return []
        return self._filtrar_componentes(
            estrutura_id, "c.nome_busca CONTAINS $termo", natureza, termo=termo_normalizado
        )

    def listar_por_periodo(
        self, estrutura_id: str, periodo: int, natureza: str | None = None
    ) -> list[dict]:
        if not isinstance(periodo, int) or periodo < 1:
            return []
        return self._filtrar_componentes(estrutura_id, "c.periodo = $periodo", natureza, periodo=periodo)

    def obter_prerequisitos(self, estrutura_id: str, codigo: str) -> list[dict]:
        return self.buscar_por_codigo(estrutura_id, codigo)

    def listar_estrutura(
        self, estrutura_id: str, natureza: str | None = None
    ) -> list[dict]:
        return self._filtrar_componentes(estrutura_id, "true", natureza)

    def listar_estruturas(self) -> list[dict]:
        return [dict(registro) for registro in self._executar(CONSULTA_ESTRUTURAS)]

    def listar_dependentes(self, estrutura_id: str, codigo: str) -> list[dict]:
        codigo = codigo.strip().upper()
        if not codigo:
            return []
        return self._filtrar_componentes(
            estrutura_id,
            "EXISTS { (c)-[:DEPENDE_DE]->(:Componente {componente_id: $alvo}) }",
            alvo=f"{estrutura_id}:{codigo}",
        )

    def listar_cadeia_pre_requisitos(self, estrutura_id: str, codigo: str) -> list[dict]:
        codigo = codigo.strip().upper()
        if not codigo:
            return []
        return [
            dict(registro)
            for registro in self._executar(CONSULTA_CADEIA, estrutura_id=estrutura_id, codigo=codigo)
        ]
