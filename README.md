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
│   ├── sqlite/             # implementação relacional (SQLite)
│   ├── mongodb/            # implementação documental (MongoDB)
│   └── neo4j/              # implementação em grafo (Neo4j)
├── dados/                  # dados curriculares conferidos pela equipe
├── docs/                   # decisões e documentação do projeto
├── modelos/                # modelos lógicos dos três bancos
├── consultas/              # integração compartilhada das consultas
├── scripts/                # ferramentas de importação e apoio
└── requirements.txt        # dependências instaladas dentro do .venv
```

Na interface, escolha o banco e a estrutura curricular. As três integrações permitem filtrar componentes por código, nome, período e natureza (obrigatória ou optativa), além de consultar pré-requisitos e componentes dependentes. O Neo4j e o SQLite mostram também a cadeia completa de pré-requisitos.

Para usar a interface com SQLite, importe a estrutura e inicie a aplicação:

```bash
python -m scripts.importar_sqlite
streamlit run app.py
```

O SQLite não precisa de serviço externo: o arquivo `dados/consulta_curricular.sqlite3` é criado pela importação. Para usar MongoDB ou Neo4j, inicie o serviço correspondente e rode `python -m scripts.importar_mongodb` ou `python -m scripts.importar_neo4j`, conforme os guias do [MongoDB](bancos/mongodb/README.md) e do [Neo4j](bancos/neo4j/README.md). O guia do [SQLite](bancos/sqlite/README.md) descreve o esquema e o uso.

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
