import altair as alt
import pandas as pd
import streamlit as st

from consultas.desempenho import comparar, montar_cenarios, resultados_divergentes, sugerir_parametros
from consultas.fabrica import MODELOS, criar_repositorio


st.set_page_config(page_title="Desempenho — Consulta Curricular TADS", page_icon="⏱️")

# Uma cor fixa por banco, na ordem de MODELOS, validada para cada tema
CORES = {
    "light": ("#2a78d6", "#eb6834", "#1baf7a"),
    "dark": ("#3987e5", "#d95926", "#199e70"),
}
NOMES_COLUNAS = {
    "consulta": "Consulta",
    "banco": "Banco",
    "mediana_ms": "Mediana (ms)",
    "media_ms": "Média (ms)",
    "minimo_ms": "Mínimo (ms)",
    "maximo_ms": "Máximo (ms)",
    "repeticoes": "Repetições",
    "resultados": "Itens devolvidos",
}


@st.cache_resource
def _obter_repositorio(modelo):
    return criar_repositorio(modelo)


def _grafico(tabela: pd.DataFrame) -> alt.Chart:
    tema = st.context.theme.type or "light"
    bancos = [modelo for modelo in MODELOS if modelo in set(tabela["banco"])]
    cores = [CORES[tema][MODELOS.index(modelo)] for modelo in bancos]
    return (
        alt.Chart(tabela)
        .mark_bar(cornerRadiusEnd=4, height={"band": 0.9})
        .encode(
            x=alt.X("mediana_ms:Q", title="Mediana do tempo de resposta (ms)"),
            y=alt.Y("consulta:N", title=None, sort=None, scale=alt.Scale(paddingInner=0.3)),
            yOffset=alt.YOffset("banco:N", sort=bancos),
            color=alt.Color(
                "banco:N",
                title="Banco",
                scale=alt.Scale(domain=bancos, range=cores),
                legend=alt.Legend(orient="top"),
            ),
            tooltip=[
                alt.Tooltip("consulta:N", title="Consulta"),
                alt.Tooltip("banco:N", title="Banco"),
                alt.Tooltip("mediana_ms:Q", title="Mediana (ms)", format=".3f"),
                alt.Tooltip("minimo_ms:Q", title="Mínimo (ms)", format=".3f"),
                alt.Tooltip("maximo_ms:Q", title="Máximo (ms)", format=".3f"),
                alt.Tooltip("resultados:Q", title="Itens devolvidos"),
            ],
        )
    )


st.title("Comparação de desempenho")
st.write("Executa as mesmas consultas em cada banco disponível e compara o tempo de resposta.")

repositorios = {}
for modelo in MODELOS:
    try:
        repositorio = _obter_repositorio(modelo)
        repositorio.listar_estruturas()
    except NotImplementedError:
        st.caption(f"{modelo}: integração ainda não disponível.")
    except Exception:
        st.caption(f"{modelo}: serviço indisponível. Confira se ele está ativo e as configurações do .env.")
    else:
        repositorios[modelo] = repositorio

if not repositorios:
    st.error("Nenhum banco está disponível para comparação.")
    st.stop()

selecionados = st.multiselect("Bancos comparados", list(repositorios), default=list(repositorios))
if not selecionados:
    st.info("Selecione ao menos um banco.")
    st.stop()

referencia = repositorios[selecionados[0]]
estruturas = referencia.listar_estruturas()
if not estruturas:
    st.info("Nenhuma estrutura curricular foi encontrada. Importe os dados antes de comparar.")
    st.stop()

estrutura_selecionada = st.selectbox(
    "Estrutura curricular",
    estruturas,
    format_func=lambda item: f"{item['curso']} — {item['periodo_inicio'] or item['ano_inicio']}",
)
estrutura_id = estrutura_selecionada["estrutura_id"]
sugestao = sugerir_parametros(referencia.listar_estrutura(estrutura_id))

with st.form("parametros_desempenho"):
    coluna_esquerda, coluna_direita = st.columns(2)
    codigo = coluna_esquerda.text_input("Código para busca e cadeia", sugestao["codigo"])
    termo = coluna_direita.text_input("Termo da busca por nome", sugestao["termo"])
    periodo = coluna_esquerda.number_input("Período", min_value=1, max_value=20, value=sugestao["periodo"])
    alvo = coluna_direita.text_input("Código para buscar dependentes", sugestao["alvo"])
    repeticoes = st.slider("Repetições medidas por consulta", min_value=5, max_value=200, value=30)
    aquecimento = st.number_input("Execuções de aquecimento (descartadas)", min_value=0, max_value=20, value=3)
    executar = st.form_submit_button("Executar comparação")

if executar:
    with st.spinner("Medindo as consultas..."):
        st.session_state["desempenho"] = comparar(
            {modelo: repositorios[modelo] for modelo in selecionados},
            montar_cenarios(estrutura_id, codigo, termo, int(periodo), alvo),
            repeticoes,
            int(aquecimento),
        )

linhas = st.session_state.get("desempenho")
if linhas:
    tabela = pd.DataFrame(linhas)
    st.subheader("Resultado")
    st.altair_chart(
        _grafico(tabela),
        width="stretch",
        alt="Barras com a mediana do tempo de resposta de cada consulta, agrupadas por banco.",
    )
    st.caption(
        "A mediana resiste a picos isolados de tempo. A cadeia de pré-requisitos só aparece "
        "para os bancos que implementam essa consulta."
    )
    for consulta in resultados_divergentes(linhas):
        st.warning(f"Os bancos devolveram quantidades diferentes de itens em “{consulta}”.")
    st.dataframe(
        tabela.rename(columns=NOMES_COLUNAS),
        hide_index=True,
        column_config={
            nome: st.column_config.NumberColumn(format="%.3f")
            for chave, nome in NOMES_COLUNAS.items()
            if chave.endswith("_ms")
        },
    )
    st.download_button(
        "Baixar CSV",
        tabela.to_csv(index=False).encode("utf-8"),
        file_name="desempenho.csv",
        mime="text/csv",
    )
