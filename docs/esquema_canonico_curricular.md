# Esquema canônico da estrutura curricular

**Versão:** 1.0  
**Uso:** referência comum para SQLite, MongoDB e Neo4j.

Este documento define o significado dos dados curriculares e uma forma única de representá-los antes de cada integrante adaptar a implementação ao seu banco. Os três bancos devem receber o mesmo conjunto de dados e devolver resultados com a mesma semântica.

## Fontes e escopo

O conjunto de referência é o curso de Tecnologia em Análise e Desenvolvimento de Sistemas da UFRN, na Escola Agrícola de Jundiaí (EAJ), estrutura SIGAA 03, iniciada em 2019.2.

- [Página pública do curso e estruturas curriculares no SIGAA](https://sigaa.ufrn.br/sigaa/public/curso/curriculo.jsf?id=94598200&lc=pt_BR): identifica a estrutura 03 como criada em 2019 e ativa.
- [Diagrama da estrutura curricular indicado no enunciado](https://sigaa.ufrn.br/sigaa/downloadArquivoPublico?idProducao=6317915&key=300ba6bebacf53bae709c86d9662d6b9): contém duas estruturas; usar a segunda página, identificada como 2019. A primeira é de 2015. O número no cabeçalho dos componentes é mantido como créditos, separado da carga horária.
- [Projeto Pedagógico do Curso (PPC), documento público do SIGAA](https://sigaa.ufrn.br/sigaa/downloadArquivoPublico?idProducao=16168549&key=2a57712a43cd58ba90a605251b8a0ef9): seção 7.4, páginas impressas 43–51, traz caracterização do curso, requisitos de integralização, períodos, cargas horárias e pré-requisitos.

**Acesso às fontes para este mapeamento:** 27/10/2026.

O PPC identifica o curso como presencial, grau Tecnologia, sede em Macaíba/RN, seis períodos e carga horária total de 2.295 horas. A estrutura 03 começou em 2019.2 e é ofertada nos turnos matutino, vespertino e noturno. A integralização discrimina 1.665 horas de componentes obrigatórios, 240 de optativos, 180 de atividades complementares, 120 de atividades integradoras e 90 de TCC.

### Regra para resolver divergências na fonte

Usar a matriz específica da estrutura 03 na seção 7.4.1 do PPC (páginas impressas 49–51) para período, carga horária e pré-requisitos. A tabela comparativa da seção 7.4.2 contém valores que divergem dessa matriz para alguns componentes, por exemplo TAD0028 e TAD0156. Para esses campos, a matriz de 7.4.1 também coincide com as caracterizações individuais dos componentes e com o catálogo público do SIGAA. Não copiar valores da comparação entre estruturas sem conferir a matriz 03.

O diagrama de 2019 é a fonte para os créditos e ajuda a conferir as relações de pré-requisito. Não converter créditos em horas quando a carga horária oficial estiver disponível. Se fontes oficiais futuras divergirem, registrar código, campo, valores e fonte antes de alterar a base canônica.

## Entidades e identificadores

### Curso

Representa o curso ao qual pertencem uma ou mais estruturas curriculares.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `curso_id` | texto | Identificador interno estável do curso. Para este projeto: `UFRN-EAJ-TADS`. |
| `nome` | texto | Nome do curso: `Análise e Desenvolvimento de Sistemas`. |
| `instituicao` | texto | Instituição: `Universidade Federal do Rio Grande do Norte`. |
| `unidade` | texto | Unidade de vínculo: `Escola Agrícola de Jundiaí (EAJ)`. |
| `municipio` | texto | Município da sede: `Macaíba/RN`. |
| `modalidade` | texto | `presencial` ou `a_distancia`, conforme a fonte. |
| `grau` | texto | Grau concedido; neste caso `tecnologo`. |

### Estrutura curricular

Representa uma versão específica do currículo de um curso. O código SIGAA não é globalmente único; deve sempre estar associado ao curso.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `estrutura_id` | texto | Identificador interno estável. Para esta estrutura: `UFRN-EAJ-TADS-03`. |
| `curso_id` | texto | Referência ao curso. |
| `codigo_sigaa` | texto | Código da estrutura na fonte: `03`. |
| `ano_inicio` | inteiro | Ano de início: `2019`. |
| `periodo_inicio` | texto | Período letivo de início: `2019.2`. Preservar como texto. |
| `ativa` | booleano | Situação informada pelo SIGAA. |
| `turnos` | lista de textos | Turnos informados: `matutino`, `vespertino`, `noturno`. |
| `duracao_semestres` | inteiro | Duração padrão: `6`. |
| `carga_horaria_total_horas` | inteiro | Total da estrutura: `2295`. |
| `fontes` | lista de objetos | URLs e data de coleta, para rastreabilidade. |

### Componente curricular na estrutura

Representa uma disciplina ou outro componente pertencente a uma versão do currículo. A ocorrência pertence à estrutura; o mesmo código em outra versão é outro registro, pois nome, carga horária, tipo ou posição podem mudar.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `componente_id` | texto | Chave estável composta: `estrutura_id:codigo`. Exemplo: `UFRN-EAJ-TADS-03:TAD0204`. |
| `codigo` | texto | Código oficial do componente, preservando zeros e letras. |
| `nome` | texto | Nome oficial, preservando acentos quando disponíveis. |
| `tipo` | texto | Tipo SIGAA, por exemplo `disciplina`, `trabalho_conclusao` ou `atividade_integradora`. Não confundir com obrigatoriedade. |
| `natureza` | texto | Relação com a estrutura: `obrigatorio` ou `optativo`. |
| `periodo` | inteiro ou nulo | Período recomendado de 1 a 6. Para opções sem período fixado, usar `null`. |
| `carga_horaria_horas` | inteiro ou nulo | Carga horária oficial em horas. Não é número de créditos. |
| `creditos` | inteiro ou nulo | Número de créditos mostrado no diagrama de 2019, quando disponível. Não usar como substituto da carga horária. |
| `modalidade` | texto ou nulo | Modalidade do componente, se a caracterização individual a informar. |
| `pre_requisitos` | expressão, lista ou nulo | Árvore lógica definida abaixo. Lista vazia significa que a fonte foi conferida e não lista pré-requisitos; `null` significa que a informação ainda não foi confirmada. |
| `co_requisitos` | expressão, lista ou nulo | Mesma representação lógica de `pre_requisitos`; lista vazia quando foi conferida e nenhum consta; `null` quando não foi confirmada. |
| `equivalencias` | lista ou nulo | Códigos equivalentes informados pela fonte; lista vazia quando foi conferida e nenhuma consta; `null` quando não foi confirmada. |

Referências de pré-requisito podem apontar para códigos de estruturas anteriores que não fazem parte da estrutura 03. Esses códigos devem ser preservados literalmente; não descartar uma condição só porque o componente não aparece na lista atual.

### Requisitos de integralização

Representam cargas horárias exigidas para concluir o curso que não correspondem necessariamente a um componente com código e período próprios. Para a estrutura 03:

| Categoria | Horas exigidas |
| --- | ---: |
| Componentes obrigatórios | 1665 |
| Componentes optativos | 240 |
| Atividades complementares | 180 |
| Atividades integradoras | 120 |
| Trabalho de conclusão de curso | 90 |
| **Total** | **2295** |

Não inventar um código de disciplina para “Atividades complementares”. Guardar esses totais como requisitos da estrutura. Quando atividades integradoras ou TCC aparecerem como componentes individuais codificados na matriz, registrar também os componentes; os totais acima são a regra geral de integralização.

## Representação lógica de pré-requisitos

Pré-requisitos podem combinar operadores `AND` e `OR`, inclusive em grupos aninhados. Usar a mesma árvore nos três bancos:

```json
{
  "operador": "AND",
  "termos": [
    {"codigo": "TAD0022"},
    {
      "operador": "OR",
      "termos": [
        {"codigo": "TAD0102"},
        {"codigo": "TAD0002"}
      ]
    }
  ]
}
```

Uma folha contém o código de um componente requerido; um grupo contém `operador` (`AND`/`OR`) e uma lista ordenada de `termos`, que podem ser folhas ou outros grupos. A ordem não altera a lógica, mas deve ser mantida para preservar a apresentação da fonte. Uma lista de códigos simples não é suficiente para expressar alternativas.

### Exemplo conferido: TAD0204

Na matriz da estrutura 03, o componente `TAD0204 — Fundamentos e Técnicas em Ciência de Dados` pertence ao 4º período, é disciplina, tem 60 horas e requer `TAD0022` **e** (`TAD0102` **ou** `TAD0002`). O diagrama de 2019 mostra 4 créditos para este componente.

```json
{
  "componente_id": "UFRN-EAJ-TADS-03:TAD0204",
  "codigo": "TAD0204",
  "nome": "Fundamentos e Técnicas em Ciência de Dados",
  "tipo": "disciplina",
  "natureza": "obrigatorio",
  "periodo": 4,
  "carga_horaria_horas": 60,
  "creditos": 4,
  "modalidade": "presencial",
  "pre_requisitos": {
    "operador": "AND",
    "termos": [
      {"codigo": "TAD0022"},
      {
        "operador": "OR",
        "termos": [
          {"codigo": "TAD0102"},
          {"codigo": "TAD0002"}
        ]
      }
    ]
  },
  "co_requisitos": [],
  "equivalencias": []
}
```

## Documento canônico de entrada

O conjunto de dados está em [dados/curriculos/tads_ufrn_2019.json](../dados/curriculos/tads_ufrn_2019.json). Ele representa uma estrutura curricular por objeto, contendo `schema_version`, `curso`, `estrutura`, `requisitos_integralizacao` e `componentes`. Cada integrante deve importar esse mesmo JSON para seu banco. Detalhes internos como nós de junção SQL, nomes de coleções e rótulos de nós no grafo não alteram esse formato nem sua semântica.

Valide a estrutura e os totais com `python -m scripts.validar_curriculo` antes de importá-la.

Valores ausentes seguem estas regras:

- `null`: campo aplicável, mas não informado ou não confirmado na fonte;
- `[]`: lista confirmada sem itens;
- não incluir campo que não se aplica ao tipo do registro;
- não preencher carga horária, crédito, período, natureza ou requisito por inferência.

Para um componente existente sem pré-requisitos confirmados, usar `pre_requisitos: []`. Para um componente cuja informação ainda não foi conferida, usar `pre_requisitos: null`.

## Mapeamento para os três bancos

### Relacional / SQLite

- `curso`: uma linha por curso, chave `curso_id`.
- `estrutura`: uma linha por versão, chave `estrutura_id`, referência a `curso_id`.
- `componente`: uma linha por componente da estrutura, chave composta (`estrutura_id`, `codigo`).
- `alocacao_curricular`: período e natureza do componente naquela estrutura; referência à chave composta do componente.
- `requisito_no`: árvore de pré-requisitos. Cada nó guarda pai, operador (`AND`/`OR`) ou código folha. Isso preserva grupos aninhados.
- `requisito_integralizacao`: categoria e horas requeridas pela estrutura.

### Documental / MongoDB

- Coleção `estruturas_curriculares`, um documento por `estrutura_id`, usado também como `_id`.
- Embutir `curso`, totais de integralização e a lista `componentes` nesse documento; cada componente leva seus campos de alocação e sua árvore de pré-requisitos.
- Essa forma atende às consultas centradas em uma estrutura e mantém cada currículo completo em um documento. O `_id` já indexa a estrutura; criar índices multikey para `componentes.codigo` e `componentes.periodo`. O campo derivado `componentes.nome_busca` guarda o nome normalizado por `consultas/normalizacao.py` para aplicar a mesma busca parcial sem acentos das outras implementações; ele não faz parte do resultado canônico.

### Grafo / Neo4j

- Nós `Curso`, `EstruturaCurricular` e `ComponenteCurricular`, identificados pelos mesmos IDs canônicos.
- Relações `TEM_ESTRUTURA` (curso para estrutura) e `CONTEM` (estrutura para componente); guardar `periodo` e `natureza` em `CONTEM`.
- Representar cada grupo lógico por um nó `GrupoRequisito` com `operador` `AND` ou `OR`; ligar grupo a grupo ou a folhas `ReferenciaComponente` contendo o código. A raiz liga-se ao componente que tem o requisito.
- Um pré-requisito antigo continua como referência pelo código mesmo se não houver nó de componente correspondente na estrutura ativa.

## Contrato mínimo para resultados equivalentes

As consultas devem receber `estrutura_id` e produzir os mesmos campos, tipos e ordenação nos três bancos. Para os resultados de componentes, usar:

```text
componente_id, codigo, nome, tipo, natureza, periodo,
carga_horaria_horas, creditos, pre_requisitos, co_requisitos, equivalencias
```

Preservar as cinco operações do MVP do documento de contexto: buscar por código, buscar por nome, listar por período, obter pré-requisitos e listar a estrutura. Busca por nome é parcial e insensível a maiúsculas, minúsculas e acentos. Para manter a regra igual, a camada Python compartilhada deve normalizar consulta e nome (minúsculas e remoção de acentos Unicode); o campo auxiliar normalizado, se armazenado para indexação, é derivado e não altera o resultado canônico. A ordenação padrão é por período crescente e depois código. Código inexistente retorna lista vazia. Um componente existente sem pré-requisitos confirmados retorna o registro com `pre_requisitos: []`.

Os módulos dos bancos devem aceitar IDs e filtros como parâmetros, sem nomes ou códigos de disciplina fixados nas consultas.

## Validações antes de carregar os três bancos

1. Confirmar com a equipe que SQLite, MongoDB e Neo4j vão usar este contrato v1.
2. Conferir a extração completa dos componentes e das árvores de pré-requisitos com as páginas 49–51 do PPC e o diagrama de 2019.
3. Verificar unicidade de `componente_id`, períodos de 1 a 6 e horas como inteiros positivos quando informadas.
4. Validar cada árvore para conter apenas `AND`, `OR` e folhas com código.
5. Conferir que os totais de integralização somam 2295 horas e que saídas equivalentes dos três bancos coincidem.
