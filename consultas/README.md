# Consultas compartilhadas

Código usado por todos os bancos, sem depender de nenhum deles em particular.

- `fabrica.py`: cria o repositório do banco escolhido. Todos os repositórios oferecem os mesmos métodos (`listar_estrutura`, `buscar_por_codigo`, `buscar_por_nome`, `listar_por_periodo`, `listar_dependentes`, `listar_estruturas` e `fechar`) e devolvem componentes com os mesmos campos, ordenados por período e código.
- `desempenho.py`: cronometra consultas e compara os bancos. Veja [docs/desempenho.md](../docs/desempenho.md).
- `normalizacao.py`: normaliza textos para busca sem acentos e sem diferenciar maiúsculas.
