# Modelo de grafo Neo4j

O modelo Neo4j representa a estrutura curricular como nós ligados por relacionamentos. Pré-requisitos deixam de ser um campo dentro do componente e passam a ser caminhos no grafo, o que torna diretas as perguntas do tipo "o que depende disto?" e "o que preciso cursar antes?", inclusive em vários níveis.

## Nós

| Rótulo | Chave única | Conteúdo |
| --- | --- | --- |
| `Curso` | `curso_id` | Campos de curso do [esquema canônico](../docs/esquema_canonico_curricular.md). |
| `Estrutura` | `estrutura_id` | Campos da estrutura, `schema_version` e `fontes_json` (lista de fontes serializada). |
| `RequisitoIntegralizacao` | — | `categoria`, `carga_horaria_horas` e `estrutura_id`. |
| `Componente` | `componente_id` | Campos canônicos do componente, `estrutura_id`, `externo` e campos auxiliares descritos abaixo. |
| `GrupoRequisito` | `grupo_id` | `operador` (`AND`/`OR`) e `estrutura_id`. |

## Relacionamentos

```text
(:Curso)-[:POSSUI_ESTRUTURA]->(:Estrutura)
(:Estrutura)-[:EXIGE_INTEGRALIZACAO]->(:RequisitoIntegralizacao)
(:Estrutura)-[:CONTEM]->(:Componente)

(:Componente)-[:EXIGE]->(:GrupoRequisito | :Componente)
(:GrupoRequisito)-[:TERMO {ordem}]->(:GrupoRequisito | :Componente)

(:Componente)-[:DEPENDE_DE]->(:Componente)
```

## Pré-requisitos como árvore

A árvore lógica do esquema canônico vira nós e arestas: cada grupo `AND`/`OR` é um `GrupoRequisito`, e cada folha é uma aresta até o `Componente` requerido. A propriedade `ordem` em `TERMO` preserva a ordem da fonte.

Exemplo de `TAD0204`, que requer `TAD0022` **e** (`TAD0102` **ou** `TAD0002`):

```text
(TAD0204)-[:EXIGE]->(AND)
                     ├─[:TERMO {ordem: 0}]->(TAD0022)
                     └─[:TERMO {ordem: 1}]->(OR)
                                             ├─[:TERMO {ordem: 0}]->(TAD0102)
                                             └─[:TERMO {ordem: 1}]->(TAD0002)  externo
```

Quando o pré-requisito é um único código, `EXIGE` aponta direto para o componente. Sem aresta `EXIGE`, o campo `pre_requisitos_conferido` diferencia lista vazia (`true`, fonte conferida) de `null` (`false`, informação não confirmada). Ao consultar, o repositório remonta a mesma árvore JSON que os outros bancos devolvem.

## Atalho `DEPENDE_DE`

Além da árvore, cada componente recebe uma aresta `DEPENDE_DE` para cada código citado nos seus pré-requisitos. A árvore guarda a lógica exata; o atalho torna simples as consultas de dependência:

```cypher
// Dependentes diretos de TAD0022
MATCH (d:Componente)-[:DEPENDE_DE]->(:Componente {componente_id: "UFRN-EAJ-TADS-03:TAD0022"})
RETURN d.codigo, d.nome

// Cadeia completa: tudo que aparece antes de TAD0204, com a menor distância
MATCH caminho = (:Componente {componente_id: "UFRN-EAJ-TADS-03:TAD0204"})-[:DEPENDE_DE*1..]->(r)
RETURN r.codigo, min(length(caminho)) AS nivel ORDER BY nivel
```

A cadeia lista todos os componentes citados, inclusive alternativas de grupos `OR`. Ela responde "o que pode ser exigido antes", não "o caminho mínimo obrigatório".

## Componentes externos

Alguns pré-requisitos citam códigos de estruturas anteriores (por exemplo, `TAD0002`). Eles viram nós `Componente` com `externo: true`, sem aresta `CONTEM`. Assim a condição é preservada literalmente, como pede o esquema canônico, mas o componente não aparece na listagem da estrutura.

## Campos auxiliares

- `nome_busca`: nome normalizado sem acentos e em minúsculas, para busca parcial com `CONTAINS`. Não é devolvido nas consultas.
- `co_requisitos_json`: co-requisitos serializados. Eles podem ser árvores, mas não são consultados como relacionamentos.
- `estrutura_id`: presente em componentes, grupos e requisitos de integralização, para remover uma estrutura inteira antes de reimportá-la.

## Restrições e índices

- Unicidade: `Curso.curso_id`, `Estrutura.estrutura_id`, `Componente.componente_id` e `GrupoRequisito.grupo_id`.
- Índices: `estrutura_id` em `Componente`, `GrupoRequisito` e `RequisitoIntegralizacao`.

A importação roda em uma única transação: remove os nós da estrutura e grava tudo de novo. Repetir a importação não duplica dados, e uma falha no meio não deixa o grafo pela metade.

## Por que um banco de grafos

A estrutura curricular é, na essência, uma rede de dependências entre disciplinas. No modelo relacional, percorrer a cadeia de pré-requisitos exige junções repetidas ou consultas recursivas; no documental, a árvore fica embutida em cada componente e a busca inversa ("quem depende de mim") precisa varrer todos os componentes. No grafo, as duas direções são o mesmo caminho percorrido em sentidos opostos, e a profundidade é só um parâmetro (`*1..`).

## Implementação

- Árvore de requisitos: [`bancos/neo4j/requisitos.py`](../bancos/neo4j/requisitos.py)
- Importação: [`bancos/neo4j/importacao.py`](../bancos/neo4j/importacao.py)
- Consultas: [`bancos/neo4j/repositorio.py`](../bancos/neo4j/repositorio.py)
