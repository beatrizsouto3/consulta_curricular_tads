# Scripts de apoio

Ferramentas de importação, teste de conexão e outras tarefas automatizadas.

- `importar_sqlite.py`: cria/atualiza `dados/consulta_curricular.sqlite3`.
- `importar_mongodb.py`: importa os currículos no MongoDB.
- `importar_neo4j.py`: importa os currículos no Neo4j.
- `testar_sqlite.py`, `testar_mongodb.py`: conferem a conexão com cada banco.
- `testar_consultas_mongodb.py`, `testar_consultas_neo4j.py`: executam consultas de exemplo contra o servidor.
- `validar_curriculo.py`: valida o JSON canônico antes da importação.
- `comparar_desempenho.py`: compara o tempo das consultas entre os bancos.
