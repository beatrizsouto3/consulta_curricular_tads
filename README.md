# Consulta à Estrutura Curricular do TADS

Aplicação para consultar a estrutura curricular do curso de TADS/UFRN e comparar, na prática, três paradigmas de banco de dados (**Relacional**, **Documental** e **Grafo**) sob o mesmo conjunto de dados e consultas.

---

## Estrutura de Pastas

```text
.
├── app.py                  # Ponto de entrada da interface web (Streamlit)
├── pages/                  # Páginas secundárias da interface (benchmark de desempenho)
├── bancos/                 # Adaptadores, conexões, esquemas e repositórios de cada banco
│   ├── sqlite/             # Implementação relacional (SQLite)
│   ├── mongodb/            # Implementação documental (MongoDB)
│   ├── neo4j/              # Implementação em grafo (Neo4j)
│   └── diagramas/          # Diagramas PlantUML dos três modelos
├── consultas/              # Fábrica de repositórios, normalização de texto e medição de tempo
├── dados/                  # Base curricular canônica em JSON e arquivo local do SQLite
├── modelos/                # Documentação da modelagem lógica de cada banco
├── docs/                   # Especificação do esquema canônico e análise de desempenho
├── scripts/                # Scripts CLI de validação, importação e testes de consulta
├── tests/                  # Testes automatizados de importação e equivalência entre bancos
├── docker-compose.yml      # Subida rápida do MongoDB e Neo4j via containers
└── requirements.txt        # Dependências Python do projeto
```

---

## Sobre o Projeto

O sistema parte de uma única fonte de verdade ([`dados/curriculos/tads_ufrn_2019.json`](dados/curriculos/tads_ufrn_2019.json)) e a importa para três bancos com modelagens distintas:

| Banco | Paradigma | Modelagem | Documentação |
| :--- | :--- | :--- | :--- |
| **SQLite** | Relacional | 10 tabelas normalizadas + árvore de requisitos em lista de adjacência | [modelos/sqlite.md](modelos/sqlite.md) |
| **MongoDB** | Documental | 1 documento por estrutura curricular com componentes e árvores embutidos | [modelos/mongodb.md](modelos/mongodb.md) |
| **Neo4j** | Grafo | Nós de curso, estrutura, componentes e grupos lógicos (`AND`/`OR`) ligados por arestas | [modelos/neo4j.md](modelos/neo4j.md) |

### Funcionalidades principais
- **Filtros combinados**: busca de disciplinas por código, nome (insensível a acentos/maiúsculas), período e natureza (obrigatória ou optativa).
- **Árvore de pré-requisitos e dependentes**: visualização das expressões lógicas `AND`/`OR`, dependentes diretos e cadeia completa de pré-requisitos.
- **Comparativo de desempenho**: bateria de testes que executa as mesmas consultas nos três bancos e compara a mediana do tempo de resposta.

---

## Como Executar

### 1. Configurar o ambiente Python (3.10+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Subir os bancos e importar os dados

- **SQLite** (não exige servidor externo):
  ```bash
  python -m scripts.importar_sqlite
  ```
- **MongoDB e Neo4j** (via Docker):
  ```bash
  docker compose up -d
  python -m scripts.importar_mongodb
  python -m scripts.importar_neo4j
  ```

### 3. Iniciar a interface web

```bash
streamlit run app.py
```

---

## Testes e Desempenho

- **Validar o JSON canônico**:
  ```bash
  python -m scripts.validar_curriculo
  ```
- **Rodar a suíte de testes**:
  ```bash
  python -m unittest discover -s tests
  ```
- **Gerar comparativo de desempenho em CSV**:
  ```bash
  python -m scripts.comparar_desempenho --saida docs/desempenho.csv
  ```
