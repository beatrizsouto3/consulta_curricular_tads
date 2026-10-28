# Modelo relacional SQLite

O modelo SQLite guarda a estrutura curricular em tabelas normalizadas. Diferentemente do documento único do MongoDB e dos caminhos do Neo4j, aqui cada entidade e cada nó de requisito é uma linha; as consultas recompõem o formato canônico por junções.

## Entidades

| Tabela | Chave | Conteúdo |
| --- | --- | --- |
| `curso` | `curso_id` | Campos de curso do [esquema canônico](../../docs/esquema_canonico_curricular.md). |
| `estrutura` | `estrutura_id` | Versão do currículo, `curso_id`, `schema_version`, código SIGAA, ano, período, situação, duração e carga total. |
| `estrutura_turno` | (`estrutura_id`, `ordem`) | Turnos, com unicidade por estrutura. |
| `estrutura_fonte` | (`estrutura_id`, `ordem`) | URL, data de coleta e escopo de cada fonte. |
| `requisito_integralizacao` | (`estrutura_id`, `ordem`) | Categoria e horas exigidas; categoria única por estrutura. |
| `componente` | (`estrutura_id`, `codigo`) | Nome, `componente_id`, tipo, carga horária, créditos, modalidade e `nome_busca` derivado. |
| `alocacao_curricular` | (`estrutura_id`, `codigo`) | Período e natureza do componente na estrutura. |
| `equivalencia` | (`estrutura_id`, `componente_codigo`, `ordem`) | Códigos equivalentes na ordem da fonte. |
| `requisito_arvore` | `arvore_id` | Uma árvore por componente e tipo (`pre_requisito`/`co_requisito`), com `conferido`. |
| `requisito_no` | `no_id` | Nó de grupo (`operador`) ou folha (`codigo`), com `pai_id` e `ordem`. |

## Relacionamentos

```text
curso 1 ── N estrutura
estrutura 1 ── N componente
componente 1 ── 1 alocacao_curricular
componente 1 ── N equivalencia
componente 1 ── N requisito_arvore
requisito_arvore 1 ── N requisito_no
requisito_no 1 ── N requisito_no   (pai_id)
```

Todas as chaves estrangeiras usam `ON DELETE CASCADE` a partir de `estrutura`, exceto a referência de `estrutura` para `curso`. Assim, reimportar uma estrutura remove e recria apenas os dados daquela versão.

## Árvore de requisitos

Cada grupo `AND`/`OR` é uma linha com `operador` preenchido e `codigo` nulo. Cada folha é uma linha com `codigo` preenchido e `operador` nulo. A raiz tem `pai_id` nulo. `ordem` preserva a posição do termo dentro do grupo. A restrição `ux_requisito_no_raiz` garante uma única raiz por árvore.

Exemplo de `TAD0204`, que exige `TAD0022` **e** (`TAD0102` **ou** `TAD0002`):

```text
requisito_arvore: componente_codigo = TAD0204, tipo = pre_requisito, conferido = 1

no_id  pai_id  ordem  operador  codigo
1      NULL    NULL   AND       NULL
2      1       0      NULL      TAD0022
3      1       1      OR        NULL
4      3       0      NULL      TAD0102
5      3       1      NULL      TAD0002
```

O código `TAD0002` é de uma estrutura anterior. Ele permanece como folha literal; não precisa existir em `componente` da estrutura atual. Isso atende à regra canônica de preservar referências antigas.

A ausência de raiz é interpretada junto com `conferido`:

- `conferido = 1` e sem nós: a fonte foi conferida e não há requisito; o resultado é `[]`;
- `conferido = 0` e sem nós: a informação não foi confirmada; o resultado é `null`.

O mesmo princípio aparece em `componente.equivalencias_conferido`.

## Índices e consultas

- `componente (estrutura_id, nome_busca)`: busca parcial normalizada.
- `alocacao_curricular (estrutura_id, natureza, periodo)`: filtros de natureza e período, além da ordenação.
- `requisito_no (codigo)`: localizar dependentes, inclusive dentro de grupos aninhados.
- `requisito_no (arvore_id, pai_id, ordem)`: reconstruir a árvore na ordem da fonte.
- Chaves primárias: estrutura e código do componente, alocação, equivalências e árvores.

As consultas montam o mesmo resultado dos outros bancos:

- **Listagem, código, nome e período** usam junções entre `componente` e `alocacao_curricular`, com ordenação por período (nulos ao final) e código.
- **Pré-requisitos e co-requisitos** são reconstruídos a partir de `requisito_no`, usando `pai_id` e `ordem`.
- **Dependentes** usam `EXISTS` sobre as folhas de pré-requisito do componente consultado.
- **Cadeia completa** usa uma CTE recursiva que percorre as folhas de cada componente, limita a profundidade e devolve o menor nível de cada código; códigos ausentes da estrutura são marcados como externos.

## Importação

[`bancos/sqlite/importacao.py`](../bancos/sqlite/importacao.py) cria o esquema, remove a estrutura anterior e grava curso, estrutura, turnos, fontes, integralização, componentes, alocações, equivalências e as duas árvores. Tudo ocorre em uma transação: uma falha no meio não deixa a estrutura pela metade, e repetir a importação não duplica dados.

## Implementação

- Esquema: [`bancos/sqlite/esquema.sql`](../bancos/sqlite/esquema.sql)
- Conexão: [`bancos/sqlite/conexao.py`](../bancos/sqlite/conexao.py)
- Importação: [`bancos/sqlite/importacao.py`](../bancos/sqlite/importacao.py)
- Consultas: [`bancos/sqlite/repositorio.py`](../bancos/sqlite/repositorio.py)
- Guia de uso: [`bancos/sqlite/README.md`](../bancos/sqlite/README.md)
