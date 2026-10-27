# Consulta à Estrutura Curricular do TADS

Aplicação acadêmica para consultar a estrutura curricular oficial do TADS e comparar implementações em diferentes paradigmas de bancos de dados.

## Preparar o ambiente

É necessário ter Python 3.10 ou superior instalado. As dependências do projeto ficam isoladas em um ambiente virtual; não é necessário instalá-las no Python global.

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para iniciar a interface, com o ambiente virtual ativado:

```bash
streamlit run app.py
```

## Estrutura inicial

```text
.
├── app.py                 # ponto de entrada da interface Streamlit
├── pages/                  # páginas extras da interface (comparação de desempenho)
├── bancos/
│   ├── sqlite/             # espaço de implementação do integrante responsável
│   ├── mongodb/            # espaço de implementação do integrante responsável
│   └── neo4j/              # espaço de implementação do integrante responsável
├── dados/                  # dados curriculares conferidos pela equipe
├── docs/                   # decisões e documentação do projeto
├── modelos/                # modelos lógicos dos três bancos
├── consultas/              # integração compartilhada das consultas
├── scripts/                # ferramentas de importação e apoio
└── requirements.txt        # dependências instaladas dentro do .venv
```

Na interface, escolha o banco e a estrutura curricular. As integrações MongoDB e Neo4j permitem filtrar componentes por código, nome, período e natureza (obrigatória ou optativa), além de consultar pré-requisitos e componentes dependentes. O Neo4j mostra também a cadeia completa de pré-requisitos. SQLite aparece no seletor, mas ainda não exibe dados enquanto sua integração é desenvolvida.

Para usar a interface, inicie os serviços e importe a estrutura conforme os guias do [MongoDB](bancos/mongodb/README.md) e do [Neo4j](bancos/neo4j/README.md). Depois execute `streamlit run app.py`.

Para cadastrar a estrutura curricular de outro curso, adicione um novo arquivo `.json` em `dados/curriculos/` seguindo o [esquema canônico](docs/esquema_canonico_curricular.md) e rode os importadores novamente. Nenhum código precisa ser alterado.

## Comparação de desempenho

A página **Desempenho**, no menu lateral da interface, executa as mesmas consultas em cada banco disponível e compara a mediana do tempo de resposta. Pelo terminal, o mesmo resultado sai em CSV:

```bash
python -m scripts.comparar_desempenho --saida docs/desempenho.csv
```

Metodologia e interpretação dos resultados estão em [docs/desempenho.md](docs/desempenho.md).

## Dependências

- `streamlit`: interface web.
- `pymongo`: conector Python para MongoDB.
- `neo4j`: driver Python para Neo4j.
- `python-dotenv`: suporte a configurações locais em arquivo `.env`.
- SQLite: disponível na biblioteca padrão do Python, sem dependência externa.

Não coloque credenciais ou arquivos `.env` no repositório. A pasta `infos/` também fica ignorada pelo Git.
