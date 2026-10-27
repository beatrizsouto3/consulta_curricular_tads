import streamlit as st

from bancos.mongodb.conexao import criar_cliente, obter_banco
from bancos.mongodb.repositorio import RepositorioMongoDB


st.set_page_config(page_title="Consulta Curricular TADS", page_icon="📚")


def _formatar_requisito(requisito, nomes):
    if isinstance(requisito, dict) and "codigo" in requisito:
        codigo = requisito["codigo"]
        return f"{codigo} — {nomes.get(codigo, 'componente fora desta estrutura')}"
    if isinstance(requisito, dict) and "termos" in requisito:
        operador = " e " if requisito.get("operador") == "AND" else " ou "
        termos = [_formatar_requisito(termo, nomes) for termo in requisito["termos"]]
        return "(" + operador.join(termos) + ")"
    if isinstance(requisito, list):
        return ", ".join(_formatar_requisito(termo, nomes) for termo in requisito)
    return "Requisito sem detalhamento disponível"


@st.cache_resource
def _obter_cliente():
    return criar_cliente()


st.title("Consulta à Estrutura Curricular do TADS")

modelo = st.selectbox("Modelo de banco de dados", ["MongoDB", "SQLite", "Neo4j"])

if modelo != "MongoDB":
    st.info(f"A integração com {modelo} ainda não está disponível.")
    st.stop()

cliente = _obter_cliente()
try:
    banco = obter_banco(cliente)
    repositorio = RepositorioMongoDB(banco)
    estruturas = repositorio.listar_estruturas()
except Exception:
    st.error("Não foi possível conectar ao MongoDB. Confira se o serviço está ativo e a URI está correta.")
    st.stop()

if not estruturas:
    st.info("Nenhuma estrutura curricular foi encontrada. Importe os dados antes de consultar.")
    st.stop()

estrutura_selecionada = st.selectbox(
    "Estrutura curricular",
    estruturas,
    format_func=lambda item: (
        f"{item['curso']} — {item['periodo_inicio'] or item['ano_inicio']}"
    ),
)
estrutura_id = estrutura_selecionada["estrutura_id"]

with st.form("filtros_curriculares"):
    tipo_busca = st.selectbox("Buscar por", ["Todos os componentes", "Código", "Nome", "Período"])
    natureza_label = st.selectbox("Natureza", ["Todas", "Obrigatórias", "Optativas"])
    natureza = {
        "Todas": None,
        "Obrigatórias": "obrigatorio",
        "Optativas": "optativo",
    }[natureza_label]
    if tipo_busca == "Período":
        valor_busca = st.number_input("Período letivo", min_value=1, max_value=20, value=1)
    elif tipo_busca == "Todos os componentes":
        valor_busca = ""
    else:
        valor_busca = st.text_input("Termo de busca")
    enviar = st.form_submit_button("Buscar")

if enviar:
    if tipo_busca == "Código":
        resultados = repositorio.buscar_por_codigo(estrutura_id, valor_busca, natureza)
    elif tipo_busca == "Nome":
        resultados = repositorio.buscar_por_nome(estrutura_id, valor_busca, natureza)
    elif tipo_busca == "Período":
        resultados = repositorio.listar_por_periodo(estrutura_id, int(valor_busca), natureza)
    else:
        resultados = repositorio.listar_estrutura(estrutura_id, natureza)
    st.session_state["resultados_curriculares"] = resultados
    st.session_state["estrutura_consultada"] = estrutura_id

if st.session_state.get("estrutura_consultada") == estrutura_id:
    resultados = st.session_state.get("resultados_curriculares", [])
    st.subheader("Componentes encontrados")
    if not resultados:
        st.info("Nenhum componente corresponde aos filtros informados.")
    else:
        st.dataframe(
            [
                {
                    "Código": item["codigo"],
                    "Componente": item["nome"],
                    "Período": item["periodo"] or "Optativa",
                    "Natureza": item["natureza"],
                    "Carga horária": item["carga_horaria_horas"],
                }
                for item in resultados
            ],
            hide_index=True,
            use_container_width=True,
        )

        nomes = {item["codigo"]: item["nome"] for item in repositorio.listar_estrutura(estrutura_id)}
        componente = st.selectbox(
            "Ver relações de um componente",
            resultados,
            format_func=lambda item: f"{item['codigo']} — {item['nome']}",
        )
        coluna_prerequisitos, coluna_dependentes = st.columns(2)
        with coluna_prerequisitos:
            st.markdown("#### Pré-requisitos")
            requisito = componente["pre_requisitos"]
            if not requisito:
                st.write("Nenhum pré-requisito registrado.")
            else:
                st.write(_formatar_requisito(requisito, nomes))
        with coluna_dependentes:
            st.markdown("#### Componentes que dependem dele")
            dependentes = repositorio.listar_dependentes(estrutura_id, componente["codigo"])
            if dependentes:
                st.dataframe(
                    [{"Código": item["codigo"], "Componente": item["nome"]} for item in dependentes],
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.write("Nenhum componente depende diretamente dele.")
