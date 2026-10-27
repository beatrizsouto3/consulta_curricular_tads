import unittest
from unittest.mock import MagicMock, Mock

from bancos.curriculo import CURRICULO_PADRAO, carregar_curriculo
from bancos.neo4j.importacao import importar_curriculo, montar_grafo
from bancos.neo4j.repositorio import RepositorioNeo4j
from bancos.neo4j.requisitos import achatar_requisito, montar_requisito


ESTRUTURA_ID = "UFRN-EAJ-TADS-03"


def _arestas_lidas(grafo: dict) -> list[dict]:
    # Reproduz o formato que a consulta Cypher devolve para cada termo de grupo
    operadores = {grupo["grupo_id"]: grupo["operador"] for grupo in grafo["grupos"]}
    return [
        {
            "grupo": termo["grupo_id"],
            "operador": operadores[termo["grupo_id"]],
            "ordem": termo["ordem"],
            "filho_grupo": termo["destino"] if termo["destino_grupo"] else None,
            "filho_codigo": None if termo["destino_grupo"] else termo["destino"].split(":")[1],
        }
        for termo in grafo["termos"]
    ]


class RequisitosNeo4jTest(unittest.TestCase):
    def test_achata_e_remonta_todas_as_arvores_do_curriculo(self):
        curriculo = carregar_curriculo(CURRICULO_PADRAO)

        for componente in curriculo["componentes"]:
            original = componente["pre_requisitos"]
            grafo = achatar_requisito(ESTRUTURA_ID, componente["componente_id"], original)
            raiz = grafo["exige"][0] if grafo["exige"] else None
            remontado = montar_requisito(
                raiz["destino"] if raiz and raiz["destino_grupo"] else None,
                raiz["destino"].split(":")[1] if raiz and not raiz["destino_grupo"] else None,
                _arestas_lidas(grafo),
                original is not None,
            )
            self.assertEqual(remontado, original, componente["codigo"])

    def test_grupo_aninhado_preserva_operadores_e_ordem(self):
        requisito = {
            "operador": "AND",
            "termos": [
                {"codigo": "TAD0022"},
                {"operador": "OR", "termos": [{"codigo": "TAD0102"}, {"codigo": "TAD0002"}]},
            ],
        }

        grafo = achatar_requisito(ESTRUTURA_ID, f"{ESTRUTURA_ID}:TAD0204", requisito)

        self.assertEqual([grupo["operador"] for grupo in grafo["grupos"]], ["AND", "OR"])
        self.assertEqual(len(grafo["termos"]), 4)
        self.assertTrue(grafo["exige"][0]["destino_grupo"])

    def test_requisito_nao_conferido_continua_nulo(self):
        self.assertIsNone(montar_requisito(None, None, [], conferido=False))
        self.assertEqual(montar_requisito(None, None, [], conferido=True), [])


class ImportacaoNeo4jTest(unittest.TestCase):
    def test_monta_grafo_com_componentes_e_externos(self):
        grafo = montar_grafo(carregar_curriculo(CURRICULO_PADRAO))

        self.assertEqual(grafo["estrutura"]["estrutura_id"], ESTRUTURA_ID)
        self.assertNotIn("fontes", grafo["estrutura"])
        self.assertEqual(len(grafo["componentes"]), 56)
        externos = {item["codigo"] for item in grafo["externos"]}
        self.assertIn("TAD0002", externos)
        self.assertNotIn("TAD0022", externos)
        self.assertEqual(grafo["componentes"][0]["nome_busca"], "fundamentos da computacao")

    def test_dependencias_apontam_para_todas_as_folhas(self):
        grafo = montar_grafo(carregar_curriculo(CURRICULO_PADRAO))

        destinos = {
            aresta["destino"]
            for aresta in grafo["depende_de"]
            if aresta["origem"] == f"{ESTRUTURA_ID}:TAD0204"
        }

        self.assertEqual(
            destinos,
            {f"{ESTRUTURA_ID}:{codigo}" for codigo in ("TAD0022", "TAD0102", "TAD0002")},
        )

    def test_importacao_cria_esquema_e_grava_em_uma_transacao(self):
        driver = MagicMock()
        sessao = driver.session.return_value.__enter__.return_value

        resumo = importar_curriculo(driver, carregar_curriculo(CURRICULO_PADRAO), "neo4j")

        driver.session.assert_called_once_with(database="neo4j")
        self.assertTrue(all("IF NOT EXISTS" in chamada.args[0] for chamada in sessao.run.call_args_list))
        sessao.execute_write.assert_called_once()
        self.assertEqual(resumo["estrutura_id"], ESTRUTURA_ID)
        self.assertEqual(resumo["componentes"], 56)

    def test_reimportacao_remove_a_estrutura_antes_de_gravar(self):
        tx = Mock()
        curriculo = carregar_curriculo(CURRICULO_PADRAO)
        driver = MagicMock()
        importar_curriculo(driver, curriculo)
        funcao, *argumentos = (
            driver.session.return_value.__enter__.return_value.execute_write.call_args.args
        )

        funcao(tx, *argumentos)

        primeiras = [chamada.args[0] for chamada in tx.run.call_args_list[:4]]
        self.assertTrue(all("DETACH DELETE" in consulta for consulta in primeiras))


class ConsultaNeo4jTest(unittest.TestCase):
    def setUp(self):
        self.driver = Mock()
        self.repositorio = RepositorioNeo4j(self.driver, "neo4j")
        self.registro = {
            "componente": {
                "componente_id": f"{ESTRUTURA_ID}:TAD0204",
                "codigo": "TAD0204",
                "nome": "Fundamentos e Técnicas em Ciência de Dados",
                "nome_busca": "fundamentos e tecnicas em ciencia de dados",
                "tipo": "disciplina",
                "natureza": "obrigatorio",
                "periodo": 4,
                "carga_horaria_horas": 60,
                "creditos": 4,
                "equivalencias": [],
                "co_requisitos_json": "[]",
                "pre_requisitos_conferido": True,
            },
            "raiz_grupo": f"{ESTRUTURA_ID}:TAD0204#1",
            "raiz_codigo": None,
            "arestas": [
                {
                    "grupo": f"{ESTRUTURA_ID}:TAD0204#1",
                    "operador": "AND",
                    "ordem": 0,
                    "filho_grupo": None,
                    "filho_codigo": "TAD0022",
                },
            ],
        }
        self.driver.execute_query.return_value = ([self.registro], None, None)

    def _parametros(self) -> dict:
        return self.driver.execute_query.call_args.args[1]

    def test_busca_por_codigo_normaliza_entrada_e_saida(self):
        resultados = self.repositorio.buscar_por_codigo(ESTRUTURA_ID, " tad0204 ")

        self.assertEqual(self._parametros()["codigo"], "TAD0204")
        self.assertEqual(resultados[0]["pre_requisitos"], {
            "operador": "AND", "termos": [{"codigo": "TAD0022"}],
        })
        self.assertEqual(resultados[0]["co_requisitos"], [])
        self.assertNotIn("nome_busca", resultados[0])
        self.assertEqual(set(resultados[0]), set(RepositorioNeo4j.CAMPOS_RESULTADO))

    def test_busca_por_nome_usa_termo_normalizado(self):
        self.repositorio.buscar_por_nome(ESTRUTURA_ID, "CIÊNCIA de DADOS")

        self.assertEqual(self._parametros()["termo"], "ciencia de dados")
        self.assertIn("CONTAINS", self.driver.execute_query.call_args.args[0])

    def test_filtro_de_natureza_e_enviado_como_parametro(self):
        self.repositorio.listar_por_periodo(ESTRUTURA_ID, 4, "obrigatorio")

        self.assertEqual(self._parametros()["natureza"], "obrigatorio")
        self.assertEqual(self._parametros()["periodo"], 4)

    def test_entradas_vazias_nao_consultam_o_banco(self):
        self.assertEqual(self.repositorio.buscar_por_codigo(ESTRUTURA_ID, "  "), [])
        self.assertEqual(self.repositorio.buscar_por_nome(ESTRUTURA_ID, ""), [])
        self.assertEqual(self.repositorio.listar_por_periodo(ESTRUTURA_ID, 0), [])
        self.driver.execute_query.assert_not_called()

    def test_dependentes_usam_id_composto_do_alvo(self):
        self.repositorio.listar_dependentes(ESTRUTURA_ID, " tad0022 ")

        self.assertEqual(self._parametros()["alvo"], f"{ESTRUTURA_ID}:TAD0022")
        self.assertIn("DEPENDE_DE", self.driver.execute_query.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
