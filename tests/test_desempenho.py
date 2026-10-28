import unittest
from unittest.mock import Mock, patch

from bancos.curriculo import CURRICULO_PADRAO, carregar_curriculo
from consultas.desempenho import (
    Cenario,
    comparar,
    cronometrar,
    medir,
    montar_cenarios,
    resultados_divergentes,
    sugerir_parametros,
)


class MedicaoTest(unittest.TestCase):
    def test_cronometrar_devolve_resultado_e_tempo_em_ms(self):
        with patch("consultas.desempenho.perf_counter", side_effect=[1.0, 1.25]):
            resultado, tempo = cronometrar(lambda valor: valor * 2, 21)

        self.assertEqual(resultado, 42)
        self.assertAlmostEqual(tempo, 250.0)

    def test_medir_descarta_aquecimento_e_usa_mediana(self):
        funcao = Mock(return_value=["a", "b"])
        # Três medidas de 1 ms, 2 ms e 9 ms: a mediana ignora o pico
        relogio = [0.0, 0.001, 0.0, 0.002, 0.0, 0.009]

        with patch("consultas.desempenho.perf_counter", side_effect=relogio):
            estatisticas = medir(funcao, "x", repeticoes=3, aquecimento=2)

        self.assertEqual(funcao.call_count, 5)
        self.assertAlmostEqual(estatisticas["mediana_ms"], 2.0)
        self.assertAlmostEqual(estatisticas["minimo_ms"], 1.0)
        self.assertAlmostEqual(estatisticas["maximo_ms"], 9.0)
        self.assertAlmostEqual(estatisticas["media_ms"], 4.0)
        self.assertEqual(estatisticas["resultados"], 2)

    def test_comparar_ignora_consulta_que_o_banco_nao_implementa(self):
        completo = Mock(spec=["listar_estrutura", "listar_cadeia_pre_requisitos"])
        completo.listar_estrutura.return_value = [1, 2]
        completo.listar_cadeia_pre_requisitos.return_value = [1]
        parcial = Mock(spec=["listar_estrutura"])
        parcial.listar_estrutura.return_value = [1, 2]
        cenarios = [
            Cenario("Estrutura", "listar_estrutura", ("E",)),
            Cenario("Cadeia", "listar_cadeia_pre_requisitos", ("E", "X")),
        ]

        linhas = comparar({"A": completo, "B": parcial}, cenarios, repeticoes=2, aquecimento=0)

        self.assertEqual(
            [(linha["consulta"], linha["banco"]) for linha in linhas],
            [("Estrutura", "A"), ("Estrutura", "B"), ("Cadeia", "A")],
        )
        completo.listar_estrutura.assert_called_with("E")

    def test_detecta_bancos_com_quantidades_diferentes(self):
        linhas = [
            {"consulta": "Estrutura", "resultados": 56},
            {"consulta": "Estrutura", "resultados": 56},
            {"consulta": "Nome", "resultados": 3},
            {"consulta": "Nome", "resultados": 2},
        ]

        self.assertEqual(resultados_divergentes(linhas), ["Nome"])


class ParametrosTest(unittest.TestCase):
    def test_sugere_parametros_a_partir_dos_dados(self):
        componentes = carregar_curriculo(CURRICULO_PADRAO)["componentes"]
        codigos = {componente["codigo"] for componente in componentes}

        parametros = sugerir_parametros(componentes)

        self.assertIn(parametros["codigo"], codigos)
        self.assertIn(parametros["alvo"], codigos)
        self.assertGreaterEqual(len(parametros["termo"]), 4)
        self.assertEqual(parametros["periodo"], 1)
        cenarios = montar_cenarios("UFRN-EAJ-TADS-03", **parametros)
        self.assertEqual(len(cenarios), 6)

    def test_estrutura_vazia_nao_quebra(self):
        self.assertEqual(sugerir_parametros([])["codigo"], "")


if __name__ == "__main__":
    unittest.main()
