# Dados do projeto

O arquivo `curriculos/tads_ufrn_2019.json` é a base canônica a importar nos três bancos. Ele representa a estrutura SIGAA 03, iniciada em 2019.2. Fontes, regras de interpretação e campos estão descritos em `docs/esquema_canonico_curricular.md`.

Valide o arquivo antes de importá-lo:

```bash
python -m scripts.validar_curriculo
```
