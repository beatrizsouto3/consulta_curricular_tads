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

Na interface, escolha o banco e a estrutura curricular. A integração MongoDB permite filtrar componentes por código, nome, período e natureza (obrigatória ou optativa), além de consultar pré-requisitos e componentes dependentes. SQLite e Neo4j aparecem no seletor, mas ainda não exibem dados enquanto suas integrações são desenvolvidas.

Para usar a interface com MongoDB, inicie o serviço e importe a estrutura conforme o [guia do MongoDB](bancos/mongodb/README.md). Depois execute `streamlit run app.py`.

## Dependências

- `streamlit`: interface web.
- `pymongo`: conector Python para MongoDB.
- `neo4j`: driver Python para Neo4j.
- `python-dotenv`: suporte a configurações locais em arquivo `.env`.
- SQLite: disponível na biblioteca padrão do Python, sem dependência externa.

Não coloque credenciais ou arquivos `.env` no repositório. A pasta `infos/` também fica ignorada pelo Git.
