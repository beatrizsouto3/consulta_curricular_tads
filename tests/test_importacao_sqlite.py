import copy
import unittest

from bancos.curriculo import CURRICULO_PADRAO, carregar_curriculo
from bancos.sqlite.conexao import criar_conexao
from bancos.sqlite.importacao import importar_curriculo
from bancos.sqlite.repositorio import RepositorioSQLite


ESTRUTURA_ID = "UFRN-EAJ-TADS-03"


class SQLiteTestCase(unittest.TestCase):
    def setUp(self):
        self.curriculo = carregar_curriculo(CURRICULO_PADRAO)
        self.conexao = criar_conexao(":memory:")
        importar_curriculo(self.conexao, self.curriculo)
        self.repositorio = RepositorioSQLite(self.conexao)
        self.addCleanup(self.repositorio.fechar)


class ImportacaoSQLiteTest(SQLiteTestCase):
    def test_importa_todos_os_componentes(self):
        componentes = self.repositorio.listar_estrutura(ESTRUTURA_ID)

        self.assertEqual(len(componentes), 56)
        self.assertEqual(
            [componente["codigo"] for componente in componentes][:2],
            ["TAD0001", "TAD0006"],
        )
        self.assertIsNone(componentes[-1]["periodo"])

    def test_reimportacao_nao_duplica_dados(self):
        importar_curriculo(self.conexao, self.curriculo)
        importar_curriculo(self.conexao, self.curriculo)

        self.assertEqual(len(self.repositorio.listar_estrutura(ESTRUTURA_ID)), 56)

    def test_lista_estruturas_devolve_booleano(self):
        estruturas = self.repositorio.listar_estruturas()

        self.assertEqual(
            estruturas,
            [
                {
                    "estrutura_id": ESTRUTURA_ID,
                    "curso": "Análise e Desenvolvimento de Sistemas",
                    "ano_inicio": 2019,
                    "periodo_inicio": "2019.2",
                    "ativa": True,
                }
            ],
        )


class ConsultaSQLiteTest(SQLiteTestCase):
    def test_busca_por_codigo_normaliza_caixa_e_espacos(self):
        resultados = self.repositorio.buscar_por_codigo(
            ESTRUTURA_ID, " tad0204 "
        )

        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["componente_id"], f"{ESTRUTURA_ID}:TAD0204")
        self.assertEqual(
            resultados[0]["nome"], "Fundamentos e Técnicas em Ciência de Dados"
        )

    def test_busca_por_nome_ignora_acentos_e_caixa(self):
        resultados = self.repositorio.buscar_por_nome(
            ESTRUTURA_ID, "CIÊNCIA de DADOS"
        )

        self.assertEqual([item["codigo"] for item in resultados], ["TAD0204"])

    def test_busca_por_nome_parcial(self):
        resultados = self.repositorio.buscar_por_nome(ESTRUTURA_ID, "programacao")
        codigos = {item["codigo"] for item in resultados}

        self.assertIn("TAD0102", codigos)
        self.assertIn("TAD0009", codigos)

    def test_lista_por_periodo_e_natureza(self):
        primeiro_periodo = self.repositorio.listar_por_periodo(ESTRUTURA_ID, 1)
        optativas = self.repositorio.listar_estrutura(ESTRUTURA_ID, "optativo")

        self.assertEqual(len(primeiro_periodo), 6)
        self.assertTrue(all(item["periodo"] == 1 for item in primeiro_periodo))
        self.assertTrue(optativas)
        self.assertTrue(all(item["natureza"] == "optativo" for item in optativas))
        self.assertTrue(all(item["periodo"] is None for item in optativas))

    def test_arvore_and_or_aninhada(self):
        componente = self.repositorio.buscar_por_codigo(ESTRUTURA_ID, "TAD0204")[0]

        self.assertEqual(
            componente["pre_requisitos"],
            {
                "operador": "AND",
                "termos": [
                    {"codigo": "TAD0022"},
                    {
                        "operador": "OR",
                        "termos": [{"codigo": "TAD0102"}, {"codigo": "TAD0002"}],
                    },
                ],
            },
        )
        self.assertEqual(componente["co_requisitos"], [])

    def test_equivalencias_preservam_ordem(self):
        componente = self.repositorio.buscar_por_codigo(ESTRUTURA_ID, "TAD0156")[0]

        self.assertEqual(componente["equivalencias"], ["TAD0056"])

    def test_dependentes_incluem_requisito_em_grupo_aninhado(self):
        dependentes = self.repositorio.listar_dependentes(ESTRUTURA_ID, "tad0002")
        codigos = {item["codigo"] for item in dependentes}

        self.assertIn("TAD0102", codigos)
        self.assertIn("TAD0204", codigos)

    def test_cadeia_de_pre_requisitos(self):
        cadeia = self.repositorio.listar_cadeia_pre_requisitos(
            ESTRUTURA_ID, "TAD0204"
        )
        por_codigo = {item["codigo"]: item for item in cadeia}

        self.assertEqual(por_codigo["TAD0022"]["nivel"], 1)
        self.assertEqual(por_codigo["TAD0022"]["nome"], "Estatística Aplicada")
        self.assertEqual(por_codigo["CCA0114"]["nivel"], 2)
        self.assertTrue(por_codigo["CCA0114"]["externo"])
        self.assertIsNone(por_codigo["CCA0114"]["nome"])

    def test_natureza_filtra_buscas(self):
        resultados = self.repositorio.buscar_por_nome(
            ESTRUTURA_ID, "programacao", "optativo"
        )

        self.assertTrue(all(item["natureza"] == "optativo" for item in resultados))

    def test_estrutura_inexistente_retorna_lista_vazia(self):
        self.assertEqual(self.repositorio.listar_estrutura("inexistente"), [])
        self.assertEqual(
            self.repositorio.buscar_por_codigo("inexistente", "TAD0001"), []
        )
        self.assertEqual(
            self.repositorio.listar_cadeia_pre_requisitos("inexistente", "TAD0204"),
            [],
        )

        conexao_vazia = criar_conexao(":memory:")
        repositorio_vazio = RepositorioSQLite(conexao_vazia)
        self.addCleanup(repositorio_vazio.fechar)
        self.assertEqual(repositorio_vazio.listar_estruturas(), [])


class SemanticaNuloVazioTest(unittest.TestCase):
    def test_distingue_requisito_nao_confirmado_de_lista_vazia(self):
        curriculo = copy.deepcopy(carregar_curriculo(CURRICULO_PADRAO))
        for componente in curriculo["componentes"]:
            if componente["codigo"] == "TAD0001":
                componente["pre_requisitos"] = None
                componente["equivalencias"] = None
            if componente["codigo"] == "TAD0201":
                componente["pre_requisitos"] = []

        conexao = criar_conexao(":memory:")
        importar_curriculo(conexao, curriculo)
        repositorio = RepositorioSQLite(conexao)
        self.addCleanup(repositorio.fechar)

        nao_confirmado = repositorio.buscar_por_codigo(ESTRUTURA_ID, "TAD0001")[0]
        vazio = repositorio.buscar_por_codigo(ESTRUTURA_ID, "TAD0201")[0]

        self.assertIsNone(nao_confirmado["pre_requisitos"])
        self.assertIsNone(nao_confirmado["equivalencias"])
        self.assertEqual(vazio["pre_requisitos"], [])
        self.assertEqual(vazio["co_requisitos"], [])


if __name__ == "__main__":
    unittest.main()
