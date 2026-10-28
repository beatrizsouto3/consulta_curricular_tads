# Neo4j

## Importar a estrutura curricular

1. Inicie o serviço Neo4j pela raiz do projeto:

```bash
docker compose up -d neo4j
```

A primeira inicialização leva alguns segundos. A senha vem de `NEO4J_PASSWORD` no `.env` (padrão `consulta_tads`) e só é aplicada quando o volume é criado. Para trocá-la depois, remova o volume com `docker compose down -v`.

2. Ative o ambiente virtual e importe os currículos:

```bash
python -m scripts.importar_neo4j
```

Sem argumentos, o script importa todos os arquivos `.json` de `dados/curriculos/`. Para importar um arquivo específico, passe o caminho: `python -m scripts.importar_neo4j dados/curriculos/outro_curso.json`. Cada estrutura é substituída por inteiro, então o script pode ser executado novamente sem duplicar dados.

A conexão usa `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` e `NEO4J_DATABASE` do `.env` ou os padrões `bolt://localhost:7687`, `neo4j`, `consulta_tads` e `neo4j`.

## Testar

Consultas contra o servidor:

```bash
python -m scripts.testar_consultas_neo4j
```

Testes de unidade, sem servidor, e teste de equivalência com o MongoDB e o SQLite, que só roda quando os bancos comparados estão disponíveis e com dados importados:

```bash
python -m unittest discover -s tests -v
```

## Explorar o grafo

O Neo4j Browser fica em <http://localhost:7474> (usuário `neo4j`). Para visualizar os pré-requisitos de uma disciplina:

```cypher
MATCH caminho = (:Componente {codigo: "TAD0204"})-[:EXIGE|TERMO*]->()
RETURN caminho
```

Na interface Streamlit, escolha **Neo4j** no seletor. Além das consultas comuns aos bancos, a seção **Cadeia completa de pré-requisitos** mostra os requisitos indiretos de um componente.

O modelo está descrito em [`modelos/neo4j.md`](../../modelos/neo4j.md). Para parar o serviço, execute `docker compose stop neo4j`.
