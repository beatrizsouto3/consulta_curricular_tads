# SQLite

Implementação relacional do projeto. O banco fica em um único arquivo local, usa apenas a biblioteca padrão do Python e não depende de serviço externo.

## Arquivo e configuração

O caminho padrão é `dados/consulta_curricular.sqlite3`. Para usar outro local, defina no `.env`:

```dotenv
SQLITE_PATH=dados/consulta_curricular.sqlite3
```

Caminhos relativos são resolvidos a partir da raiz do projeto. O arquivo é gerado localmente e está coberto pelo `.gitignore` (`*.sqlite3`), portanto não deve ser versionado.

## Criar ou atualizar o banco

```bash
python -m scripts.validar_curriculo
python -m scripts.importar_sqlite
```

O importador cria o esquema se ainda não existir e grava todos os currículos de `dados/curriculos/` (ou os arquivos passados como argumento). Também é possível conferir se o arquivo abre:

```bash
python -m scripts.testar_sqlite
```

A importação é transacional e pode ser repetida. Para cada `estrutura_id`, os dados anteriores são removidos em cascata e gravados novamente; repetir não duplica componentes nem requisitos.

## Esquema

O DDL completo está em [`esquema.sql`](esquema.sql). As tabelas seguem o [esquema canônico](../../docs/esquema_canonico_curricular.md):

| Tabela | Conteúdo |
| --- | --- |
| `curso` | Dados do curso, chave `curso_id`. |
| `estrutura` | Versão do currículo, chave `estrutura_id`, referência ao curso e `schema_version`. |
| `estrutura_turno` | Turnos ofertados, na ordem da fonte. |
| `estrutura_fonte` | URLs, data de coleta e escopo das fontes. |
| `requisito_integralizacao` | Categoria e carga horária exigida pela estrutura. |
| `componente` | Ocorrência do componente na estrutura, chave composta (`estrutura_id`, `codigo`), incluindo `componente_id` único e `nome_busca`. |
| `alocacao_curricular` | Período e natureza do componente naquela estrutura. |
| `equivalencia` | Códigos equivalentes, preservando a ordem da fonte. |
| `requisito_arvore` | Uma árvore de pré-requisitos e uma de co-requisitos por componente, com a marca `conferido`. |
| `requisito_no` | Nós da árvore em lista de adjacência: grupo `AND`/`OR` ou folha com código. |

```text
curso 1 ── N estrutura 1 ── N componente 1 ── 1 alocacao_curricular
                 │                 ├── N equivalencia
                 │                 └── 2 requisito_arvore 1 ── N requisito_no
                 ├── N estrutura_turno
                 ├── N estrutura_fonte
                 └── N requisito_integralizacao
```

Decisões do modelo:

- **Chave composta do componente.** O mesmo código em outra estrutura é outro registro, como exige o contrato. `componente_id` continua único e é devolvido nas consultas.
- **Árvore em `requisito_no`.** Cada grupo guarda `operador` (`AND`/`OR`) e cada folha guarda `codigo`. `pai_id` e `ordem` preservam grupos aninhados e a ordem da fonte. Códigos de estruturas anteriores ficam gravados literalmente, sem chave estrangeira para `componente`.
- **Nulo diferente de vazio.** `requisito_arvore.conferido` registra se a fonte foi conferida. Sem raiz e `conferido = 1`, a consulta devolve `[]`; sem raiz e `conferido = 0`, devolve `null`. O mesmo vale para `equivalencias_conferido` em `componente`.
- **Busca por nome.** `nome_busca` guarda o nome normalizado por [`consultas/normalizacao.py`](../../consultas/normalizacao.py). É um campo derivado, usado só na busca parcial sem acentos e sem diferença de caixa, e não aparece no resultado.
- **Índices.** Há índices para nome normalizado, natureza/período, código de requisito e a árvore por pai/ordem. A chave primária composta já atende a busca por estrutura e código.
- **Remoção em cascata.** Apagar uma estrutura remove alocações, equivalências, árvores e nós automaticamente. As chaves estrangeiras são ativadas em cada conexão.

## Consultas

O repositório implementa o mesmo contrato dos outros bancos:

| Método | Resultado |
| --- | --- |
| `listar_estruturas()` | Estruturas disponíveis com curso, ano, período e situação. |
| `listar_estrutura(estrutura_id, natureza=None)` | Componentes da estrutura, ordenados por período e código. |
| `buscar_por_codigo(estrutura_id, codigo, natureza=None)` | Busca exata, ignorando espaços e caixa. |
| `buscar_por_nome(estrutura_id, termo, natureza=None)` | Busca parcial sem acentos e sem diferença de caixa. |
| `listar_por_periodo(estrutura_id, periodo, natureza=None)` | Componentes do período. |
| `obter_prerequisitos(estrutura_id, codigo)` | Registro do componente com a árvore de pré-requisitos. |
| `listar_dependentes(estrutura_id, codigo)` | Componentes cuja árvore menciona o código, inclusive em grupos aninhados. |
| `listar_cadeia_pre_requisitos(estrutura_id, codigo)` | Todos os requisitos diretos e indiretos, com nível e indicação de componente externo. |
| `fechar()` | Fecha a conexão. |

Os componentes devolvem sempre os campos do contrato: `componente_id`, `codigo`, `nome`, `tipo`, `natureza`, `periodo`, `carga_horaria_horas`, `creditos`, `pre_requisitos`, `co_requisitos` e `equivalencias`. Componentes sem período, como as optativas, aparecem ao final.

Uso direto:

```python
from consultas.fabrica import criar_repositorio

repositorio = criar_repositorio("SQLite")
try:
    print(repositorio.listar_estruturas())
    componentes = repositorio.buscar_por_nome("UFRN-EAJ-TADS-03", "programacao")
finally:
    repositorio.fechar()
```

A interface Streamlit já usa esse caminho pela fábrica: basta selecionar **SQLite** em `streamlit run app.py`.

## Testes

```bash
python -m unittest tests.test_importacao_sqlite -v
```

Os testes usam banco em memória e não dependem de serviço externo. `tests/test_equivalencia_bancos.py` também compara o SQLite com MongoDB e Neo4j quando esses bancos estão ativos e importados.

## Implementação

- Conexão: [`conexao.py`](conexao.py)
- Esquema: [`esquema.sql`](esquema.sql) e [`esquema.py`](esquema.py)
- Importação: [`importacao.py`](importacao.py)
- Consultas: [`repositorio.py`](repositorio.py)
- Modelo lógico: [`modelos/sqlite.md`](../../modelos/sqlite.md)
