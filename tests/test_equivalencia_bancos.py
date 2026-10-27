import unittest

from consultas.fabrica import criar_repositorio


ESTRUTURA_ID = "UFRN-EAJ-TADS-03"
REFERENCIA = "MongoDB"
COMPARADOS = ("Neo4j",)


def _conectar(modelo: str, abertos: list):
    try:
        repositorio = criar_repositorio(modelo)
        abertos.append(repositorio)
        estruturas = repositorio.listar_estruturas()
    except Exception as erro:
        raise unittest.SkipTest(f"{modelo} indisponível: {erro.__class__.__name__}")
    if ESTRUTURA_ID not in {estrutura["estrutura_id"] for estrutura in estruturas}:
        raise unittest.SkipTest(f"{ESTRUTURA_ID} não foi importada no {modelo}.")
    return repositorio


# Exige os serviços ativos e o currículo importado; caso contrário, é pulado
class EquivalenciaBancosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.abertos = []
        cls.addClassCleanup(lambda: [repositorio.fechar() for repositorio in cls.abertos])
        cls.referencia = _conectar(REFERENCIA, cls.abertos)
        cls.comparados = {modelo: _conectar(modelo, cls.abertos) for modelo in COMPARADOS}

    def _comparar(self, metodo: str, *argumentos):
        esperado = getattr(self.referencia, metodo)(*argumentos)
        for modelo, repositorio in self.comparados.items():
            with self.subTest(banco=modelo, consulta=metodo, argumentos=argumentos):
                self.assertEqual(getattr(repositorio, metodo)(*argumentos), esperado)

    def test_estrutura_completa_e_por_natureza(self):
        self._comparar("listar_estrutura", ESTRUTURA_ID)
        self._comparar("listar_estrutura", ESTRUTURA_ID, "optativo")

    def test_buscas_por_codigo_nome_e_periodo(self):
        self._comparar("buscar_por_codigo", ESTRUTURA_ID, "TAD0204")
        self._comparar("buscar_por_nome", ESTRUTURA_ID, "programacao")
        self._comparar("buscar_por_nome", ESTRUTURA_ID, "dados", "obrigatorio")
        for periodo in range(1, 7):
            self._comparar("listar_por_periodo", ESTRUTURA_ID, periodo)

    def test_dependentes_de_todos_os_componentes(self):
        for componente in self.referencia.listar_estrutura(ESTRUTURA_ID):
            self._comparar("listar_dependentes", ESTRUTURA_ID, componente["codigo"])
        self._comparar("listar_dependentes", ESTRUTURA_ID, "TAD0002")

    def test_lista_de_estruturas(self):
        esperado = sorted(self.referencia.listar_estruturas(), key=lambda item: item["estrutura_id"])
        for modelo, repositorio in self.comparados.items():
            with self.subTest(banco=modelo):
                self.assertEqual(repositorio.listar_estruturas(), esperado)


if __name__ == "__main__":
    unittest.main()
