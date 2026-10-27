# Modelo documental MongoDB

O modelo MongoDB guarda uma estrutura curricular completa em um documento. Essa organização mantém juntos os dados consultados em conjunto: curso, versão da matriz, requisitos de integralização e componentes.

## Coleção

`estruturas_curriculares` contém um documento para cada estrutura curricular. O campo `_id` recebe o valor de `estrutura.estrutura_id`, garantindo uma chave única por versão do currículo.

```text
estruturas_curriculares
└── _id: estrutura_id
    ├── schema_version
    ├── curso
    ├── estrutura
    ├── requisitos_integralizacao[]
    └── componentes[]
```

`curso`, `estrutura`, `requisitos_integralizacao` e `componentes` seguem os campos definidos no [esquema canônico](../docs/esquema_canonico_curricular.md) e nos dados de [TADS/UFRN 2019](../dados/curriculos/tads_ufrn_2019.json).

## Componentes e pré-requisitos

Cada item de `componentes` representa uma disciplina, atividade ou outro componente curricular. Seus dados de período e natureza ficam no próprio item, pois pertencem àquela estrutura. Pré-requisitos são embutidos como árvores para preservar grupos lógicos `AND` e `OR`:

```json
{
  "componente_id": "UFRN-EAJ-TADS-03:TAD0204",
  "codigo": "TAD0204",
  "nome": "Fundamentos e Técnicas em Ciência de Dados",
  "natureza": "obrigatorio",
  "periodo": 4,
  "pre_requisitos": {
    "operador": "AND",
    "termos": [
      {"codigo": "TAD0022"},
      {
        "operador": "OR",
        "termos": [{"codigo": "TAD0102"}, {"codigo": "TAD0002"}]
      }
    ]
  }
}
```

Uma folha `{ "codigo": "..." }` é uma referência a um requisito. Ela pode apontar para um código que não aparece na estrutura ativa, pois alguns requisitos vêm de currículos anteriores.

## Campo auxiliar de busca

O importador acrescenta `nome_busca` a cada componente. É o nome normalizado sem acentos e em minúsculas, usado na busca parcial. Esse campo é derivado, não pertence ao contrato canônico e não é devolvido nas consultas.

## Índices e consultas

- `_id`: índice único criado pelo MongoDB para localizar uma estrutura.
- `componentes.codigo`: índice multikey para localizar componentes pelo código.
- `componentes.periodo`: índice multikey para filtrar componentes por período.
- natureza: filtro aplicado junto à busca por código, nome ou período.
- pré-requisitos: árvore retornada no componente consultado.
- dependentes: componentes da estrutura cujas árvores de pré-requisitos mencionam o código consultado, inclusive dentro de grupos aninhados.

As buscas devolvem os campos canônicos de componente, ordenados por período e código; componentes sem período, como optativas, aparecem ao final. A importação usa `replace_one` com `upsert`, identificando o documento por `_id`, portanto pode ser repetida sem criar cópias da mesma estrutura.

## Implementação

- Importação: [`bancos/mongodb/importacao.py`](../bancos/mongodb/importacao.py)
- Consultas: [`bancos/mongodb/repositorio.py`](../bancos/mongodb/repositorio.py)
- Interface: [`app.py`](../app.py)
