# Comparação de desempenho

A comparação executa as mesmas consultas, com os mesmos parâmetros, em cada banco disponível e mede o tempo de resposta do ponto de vista da aplicação: ida ao banco, execução e conversão do resultado para o formato comum dos repositórios.

## Como executar

Com os serviços ativos e os dados importados em cada banco:

```bash
python -m scripts.comparar_desempenho --saida docs/desempenho.csv
```

Opções: `--bancos SQLite MongoDB Neo4j` limita os bancos, `--estrutura` escolhe a estrutura, `--repeticoes` e `--aquecimento` controlam as execuções. Bancos indisponíveis ou ainda não implementados são ignorados com um aviso.

Na interface, a página **Desempenho** (menu lateral do `streamlit run app.py`) faz a mesma medição, mostra o gráfico e a tabela e permite baixar o CSV. A página principal também mostra o tempo de cada busca feita.

## Metodologia

- **Mesmas consultas, mesmos parâmetros.** Cada consulta é um cenário (`consultas/desempenho.py`) chamado pelo mesmo nome de método em todos os repositórios. O teste `tests/test_equivalencia_bancos.py` garante que os bancos devolvem o mesmo resultado, então a comparação mede só o tempo.
- **Parâmetros tirados dos dados.** O código consultado é o componente com mais pré-requisitos; o alvo dos dependentes é o componente mais exigido por outros. Nada é fixo no TADS, então a comparação funciona com outro curso.
- **Aquecimento.** As primeiras execuções (3 por padrão) são descartadas, porque incluem abertura de conexão e caches frios, que não representam o uso contínuo.
- **Mediana.** Cada consulta é medida 30 vezes por padrão. A mediana é o valor principal porque um pico isolado (o sistema operacional ocupado, por exemplo) distorce a média, mas não a mediana. Mínimo, máximo e média ficam no CSV para referência.
- **Relógio.** `time.perf_counter()`, o relógio de maior resolução do Python para medir intervalos.
- **Consultas exclusivas.** A cadeia de pré-requisitos é implementada no Neo4j e no SQLite; no MongoDB ela não existe como método e não entra na comparação desse banco.

## Exemplo de execução

27/10/2026, máquina de desenvolvimento, MongoDB 7.0 e Neo4j 5.26 em Docker local, 30 repetições:

| Consulta | MongoDB | Neo4j | Itens |
| --- | ---: | ---: | ---: |
| Estrutura completa | 1,240 ms | 7,948 ms | 56 |
| Busca por código | 0,572 ms | 3,771 ms | 1 |
| Busca por nome | 0,637 ms | 4,099 ms | 2 |
| Componentes do período | 0,873 ms | 4,759 ms | 6 |
| Dependentes diretos | 0,960 ms | 4,916 ms | 7 |
| Cadeia de pré-requisitos | — | 3,703 ms | 7 |

Os números variam com a máquina; gere os seus antes de apresentar.

## Como interpretar

- **Volume pequeno favorece o documento único.** O MongoDB lê um único documento com a estrutura inteira; com 56 componentes, isso é quase só o custo de rede.
- **O Neo4j tem um custo fixo por consulta.** Uma consulta vazia (`RETURN 1`) levou 2,5 ms, contra 0,35 ms de um `ping` no MongoDB, porque cada chamada abre sessão e transação pelo protocolo Bolt. Boa parte do tempo do grafo é esse custo, não a travessia.
- **A vantagem do grafo é a pergunta, não o cronômetro.** A cadeia completa de pré-requisitos é uma única consulta Cypher com profundidade variável; no documento, exigiria percorrer as árvores repetidamente na aplicação.
