# MongoDB

## Importar a estrutura curricular

1. Inicie o serviço MongoDB pela raiz do projeto:

```bash
docker compose up -d mongodb
```

2. Ative o ambiente virtual e importe o JSON canônico:

```bash
python -m scripts.importar_mongodb
```

Sem argumentos, o script importa todos os arquivos `.json` de `dados/curriculos/`; para um arquivo específico, passe o caminho como argumento. Ele grava um documento por estrutura na coleção `estruturas_curriculares`. Ele pode ser executado novamente sem duplicar o currículo. A conexão usa `MONGODB_URI` e `MONGODB_DATABASE` do `.env` ou os padrões `mongodb://localhost:27017/` e `consulta_curricular_tads`.

Depois da importação, inicie a interface na raiz do projeto com `streamlit run app.py`. Ela permite escolher a estrutura, filtrar componentes por código, nome, período ou natureza e visualizar pré-requisitos e dependentes diretos. A busca inversa considera os grupos de requisitos `AND` e `OR`.

Rode o importador novamente depois de mudar os dados ou o formato dos documentos. Depois teste as consultas contra o servidor:

```bash
python -m scripts.testar_consultas_mongodb
```

Para testar a conexão sem importar dados, execute `python -m scripts.testar_mongodb`. Para parar o serviço, execute `docker compose stop mongodb`.

Os testes do importador podem ser executados sem servidor MongoDB:

```bash
python -m unittest discover -s tests -v
```

O Compose usa MongoDB 7.0.45 para contornar a incompatibilidade de inicialização observada entre MongoDB 8.0 e o kernel Linux deste ambiente.
