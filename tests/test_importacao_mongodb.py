import unittest
from unittest.mock import Mock

from bancos.mongodb.importacao import (
    CURRICULO_PADRAO,
    carregar_curriculo,
    importar_curriculo,
    montar_documento,
)
from bancos.mongodb.repositorio import RepositorioMongoDB
from consultas.normalizacao import normalizar_texto


class ImportacaoMongoDBTest(unittest.TestCase):
    def test_monta_documento_com_id_da_estrutura(self):
        curriculo = carregar_curriculo(CURRICULO_PADRAO)

        documento = montar_documento(curriculo)

        self.assertEqual(documento["_id"], "UFRN-EAJ-TADS-03")
        self.assertEqual(len(documento["componentes"]), 56)
        self.assertEqual(documento["curso"]["curso_id"], "UFRN-EAJ-TADS")
        self.assertEqual(documento["componentes"][0]["nome_busca"], "fundamentos da computacao")

    def test_substitui_por_id_com_upsert_e_cria_indices(self):
        curriculo = carregar_curriculo(CURRICULO_PADRAO)
        colecao = Mock()
        banco = {"estruturas_curriculares": colecao}

        importar_curriculo(banco, curriculo)

        colecao.create_index.assert_any_call("componentes.codigo")
        colecao.create_index.assert_any_call("componentes.periodo")
        colecao.replace_one.assert_called_once()
        filtro, documento = colecao.replace_one.call_args.args
        self.assertEqual(filtro, {"_id": "UFRN-EAJ-TADS-03"})
        self.assertEqual(documento["_id"], filtro["_id"])
        self.assertTrue(colecao.replace_one.call_args.kwargs["upsert"])

    def test_reimportacao_reutiliza_a_mesma_chave(self):
        curriculo = carregar_curriculo(CURRICULO_PADRAO)
        colecao = Mock()
        banco = {"estruturas_curriculares": colecao}

        importar_curriculo(banco, curriculo)
        importar_curriculo(banco, curriculo)

        self.assertEqual(colecao.replace_one.call_count, 2)
        filtros = [chamada.args[0] for chamada in colecao.replace_one.call_args_list]
        self.assertEqual(filtros, [{"_id": "UFRN-EAJ-TADS-03"}] * 2)


class ConsultaMongoDBTest(unittest.TestCase):
    def setUp(self):
        self.colecao = Mock()
        self.repositorio = RepositorioMongoDB({"estruturas_curriculares": self.colecao})
        self.componente = {
            "componente_id": "UFRN-EAJ-TADS-03:TAD0204",
            "codigo": "TAD0204",
            "nome": "Fundamentos e Técnicas em Ciência de Dados",
            "nome_busca": "fundamentos e tecnicas em ciencia de dados",
            "tipo": "disciplina",
            "natureza": "obrigatorio",
            "periodo": 4,
            "carga_horaria_horas": 60,
            "creditos": 4,
            "pre_requisitos": {"operador": "AND", "termos": [{"codigo": "TAD0022"}]},
            "co_requisitos": [],
            "equivalencias": [],
        }

    def test_busca_por_codigo_e_normaliza_saida(self):
        self.colecao.aggregate.return_value = iter([{"componentes": [self.componente]}])

        resultados = self.repositorio.buscar_por_codigo("UFRN-EAJ-TADS-03", " tad0204 ")

        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["codigo"], "TAD0204")
        self.assertNotIn("nome_busca", resultados[0])
        pipeline = self.colecao.aggregate.call_args.args[0]
        self.assertEqual(pipeline[0]["$match"]["_id"], "UFRN-EAJ-TADS-03")
        self.assertEqual(pipeline[0]["$match"]["componentes.codigo"], "TAD0204")

    def test_busca_por_nome_normaliza_acentos_e_caixa(self):
        self.colecao.aggregate.return_value = iter([{"componentes": [self.componente]}])

        resultados = self.repositorio.buscar_por_nome("UFRN-EAJ-TADS-03", "CIÊNCIA de DADOS")

        self.assertEqual(resultados[0]["codigo"], "TAD0204")
        self.assertEqual(normalizar_texto("  CIÊNCIA   de Dados "), "ciencia de dados")
        pipeline = self.colecao.aggregate.call_args.args[0]
        self.assertIn("$regexMatch", pipeline[1]["$project"]["componentes"]["$filter"]["cond"])

    def test_busca_por_codigo_aplica_filtro_de_natureza(self):
        self.colecao.aggregate.return_value = iter([{"componentes": [self.componente]}])

        self.repositorio.buscar_por_codigo("UFRN-EAJ-TADS-03", "TAD0204", "obrigatorio")

        pipeline = self.colecao.aggregate.call_args.args[0]
        self.assertEqual(pipeline[0]["$match"]["componentes.natureza"], "obrigatorio")
        self.assertEqual(
            pipeline[1]["$project"]["componentes"]["$filter"]["cond"]["$and"][1],
            {"$eq": ["$$componente.natureza", "obrigatorio"]},
        )

    def test_lista_estrutura_ordena_periodo_e_codigo(self):
        optativa = {**self.componente, "codigo": "TAD0010", "periodo": None}
        segundo_periodo = {**self.componente, "codigo": "TAD0009", "periodo": 2}
        primeiro_periodo = {**self.componente, "codigo": "TAD0001", "periodo": 1}
        self.colecao.find_one.return_value = {
            "componentes": [optativa, segundo_periodo, primeiro_periodo]
        }

        resultados = self.repositorio.listar_estrutura("UFRN-EAJ-TADS-03")

        self.assertEqual([item["codigo"] for item in resultados], ["TAD0001", "TAD0009", "TAD0010"])

    def test_lista_estrutura_filtra_por_natureza(self):
        optativa = {**self.componente, "codigo": "TAD0010", "natureza": "optativo"}
        self.colecao.find_one.return_value = {"componentes": [self.componente, optativa]}

        resultados = self.repositorio.listar_estrutura("UFRN-EAJ-TADS-03", "optativo")

        self.assertEqual([item["codigo"] for item in resultados], ["TAD0010"])

    def test_estrutura_ausente_retorna_lista_vazia(self):
        self.colecao.find_one.return_value = None

        self.assertEqual(self.repositorio.listar_estrutura("inexistente"), [])

    def test_lista_estruturas_retorna_identificacao_e_ano(self):
        self.colecao.find.return_value = [{
            "_id": "UFRN-EAJ-TADS-03",
            "curso": {"nome": "Análise e Desenvolvimento de Sistemas"},
            "estrutura": {"ano_inicio": 2019, "periodo_inicio": "2019.2", "ativa": True},
        }]

        estruturas = self.repositorio.listar_estruturas()

        self.assertEqual(estruturas[0]["estrutura_id"], "UFRN-EAJ-TADS-03")
        self.assertEqual(estruturas[0]["periodo_inicio"], "2019.2")

    def test_lista_dependentes_encontra_requisito_em_grupo_aninhado(self):
        dependente = {
            **self.componente,
            "codigo": "TAD0156",
            "pre_requisitos": {
                "operador": "AND",
                "termos": [
                    {"operador": "OR", "termos": [{"codigo": "TAD0102"}, {"codigo": "TAD0002"}]},
                    {"codigo": "TAD0204"},
                ],
            },
        }
        sem_relacao = {**self.componente, "codigo": "TAD0001", "pre_requisitos": []}
        self.colecao.find_one.return_value = {"componentes": [dependente, sem_relacao]}

        resultados = self.repositorio.listar_dependentes("UFRN-EAJ-TADS-03", " tad0204 ")

        self.assertEqual([item["codigo"] for item in resultados], ["TAD0156"])


if __name__ == "__main__":
    unittest.main()
