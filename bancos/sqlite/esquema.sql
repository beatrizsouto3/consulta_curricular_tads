-- Esquema relacional do banco SQLite da consulta curricular.
-- As entidades e os campos seguem docs/esquema_canonico_curricular.md.
-- A importação pode ser repetida: os dados de uma estrutura são removidos e
-- gravados novamente dentro da mesma transação.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS curso (
    curso_id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    instituicao TEXT NOT NULL,
    unidade TEXT NOT NULL,
    municipio TEXT NOT NULL,
    modalidade TEXT NOT NULL,
    grau TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS estrutura (
    estrutura_id TEXT PRIMARY KEY,
    curso_id TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    codigo_sigaa TEXT NOT NULL,
    ano_inicio INTEGER NOT NULL,
    periodo_inicio TEXT NOT NULL,
    ativa INTEGER NOT NULL CHECK (ativa IN (0, 1)),
    duracao_semestres INTEGER NOT NULL CHECK (duracao_semestres > 0),
    carga_horaria_total_horas INTEGER NOT NULL CHECK (carga_horaria_total_horas > 0),
    FOREIGN KEY (curso_id) REFERENCES curso (curso_id) ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS estrutura_turno (
    estrutura_id TEXT NOT NULL,
    ordem INTEGER NOT NULL CHECK (ordem >= 0),
    turno TEXT NOT NULL,
    PRIMARY KEY (estrutura_id, ordem),
    UNIQUE (estrutura_id, turno),
    FOREIGN KEY (estrutura_id) REFERENCES estrutura (estrutura_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS estrutura_fonte (
    estrutura_id TEXT NOT NULL,
    ordem INTEGER NOT NULL CHECK (ordem >= 0),
    url TEXT NOT NULL,
    coletada_em TEXT,
    escopo TEXT,
    PRIMARY KEY (estrutura_id, ordem),
    FOREIGN KEY (estrutura_id) REFERENCES estrutura (estrutura_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS requisito_integralizacao (
    estrutura_id TEXT NOT NULL,
    ordem INTEGER NOT NULL CHECK (ordem >= 0),
    categoria TEXT NOT NULL,
    carga_horaria_horas INTEGER NOT NULL CHECK (carga_horaria_horas > 0),
    PRIMARY KEY (estrutura_id, ordem),
    UNIQUE (estrutura_id, categoria),
    FOREIGN KEY (estrutura_id) REFERENCES estrutura (estrutura_id) ON DELETE CASCADE
);

-- Cada ocorrência do componente pertence a uma estrutura. O componente_id
-- canônico é único, mas a chave relacional é (estrutura_id, codigo).
CREATE TABLE IF NOT EXISTS componente (
    estrutura_id TEXT NOT NULL,
    codigo TEXT NOT NULL,
    componente_id TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    nome_busca TEXT NOT NULL,
    tipo TEXT NOT NULL,
    carga_horaria_horas INTEGER CHECK (carga_horaria_horas > 0),
    creditos INTEGER CHECK (creditos >= 0),
    modalidade TEXT,
    equivalencias_conferido INTEGER NOT NULL CHECK (equivalencias_conferido IN (0, 1)),
    PRIMARY KEY (estrutura_id, codigo),
    FOREIGN KEY (estrutura_id) REFERENCES estrutura (estrutura_id) ON DELETE CASCADE
);

-- Período e natureza pertencem à alocação do componente naquela estrutura.
CREATE TABLE IF NOT EXISTS alocacao_curricular (
    estrutura_id TEXT NOT NULL,
    codigo TEXT NOT NULL,
    periodo INTEGER CHECK (periodo IS NULL OR periodo > 0),
    natureza TEXT NOT NULL CHECK (natureza IN ('obrigatorio', 'optativo')),
    PRIMARY KEY (estrutura_id, codigo),
    FOREIGN KEY (estrutura_id, codigo)
        REFERENCES componente (estrutura_id, codigo) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS equivalencia (
    estrutura_id TEXT NOT NULL,
    componente_codigo TEXT NOT NULL,
    ordem INTEGER NOT NULL CHECK (ordem >= 0),
    codigo_equivalente TEXT NOT NULL,
    PRIMARY KEY (estrutura_id, componente_codigo, ordem),
    UNIQUE (estrutura_id, componente_codigo, codigo_equivalente),
    FOREIGN KEY (estrutura_id, componente_codigo)
        REFERENCES componente (estrutura_id, codigo) ON DELETE CASCADE
);

-- Uma árvore por componente e por tipo de requisito. O campo conferido
-- distingue lista vazia conferida (1) de informação ainda não confirmada (0).
CREATE TABLE IF NOT EXISTS requisito_arvore (
    arvore_id INTEGER PRIMARY KEY,
    estrutura_id TEXT NOT NULL,
    componente_codigo TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('pre_requisito', 'co_requisito')),
    conferido INTEGER NOT NULL CHECK (conferido IN (0, 1)),
    UNIQUE (estrutura_id, componente_codigo, tipo),
    FOREIGN KEY (estrutura_id, componente_codigo)
        REFERENCES componente (estrutura_id, codigo) ON DELETE CASCADE
);

-- Árvore AND/OR em lista de adjacência: um nó é grupo (operador) ou folha
-- (código). pai_id nulo identifica a raiz; ordem preserva a ordem da fonte.
CREATE TABLE IF NOT EXISTS requisito_no (
    no_id INTEGER PRIMARY KEY,
    arvore_id INTEGER NOT NULL,
    pai_id INTEGER,
    ordem INTEGER CHECK (ordem IS NULL OR ordem >= 0),
    operador TEXT CHECK (operador IN ('AND', 'OR')),
    codigo TEXT,
    CHECK (
        (operador IS NOT NULL AND codigo IS NULL)
        OR (operador IS NULL AND codigo IS NOT NULL)
    ),
    FOREIGN KEY (arvore_id) REFERENCES requisito_arvore (arvore_id) ON DELETE CASCADE,
    FOREIGN KEY (pai_id) REFERENCES requisito_no (no_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_componente_nome_busca
    ON componente (estrutura_id, nome_busca);

CREATE INDEX IF NOT EXISTS ix_alocacao_natureza_periodo
    ON alocacao_curricular (estrutura_id, natureza, periodo);

CREATE INDEX IF NOT EXISTS ix_requisito_no_codigo
    ON requisito_no (codigo);

CREATE INDEX IF NOT EXISTS ix_requisito_no_arvore
    ON requisito_no (arvore_id, pai_id, ordem);

CREATE UNIQUE INDEX IF NOT EXISTS ux_requisito_no_raiz
    ON requisito_no (arvore_id) WHERE pai_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_requisito_no_ordem
    ON requisito_no (arvore_id, pai_id, ordem) WHERE pai_id IS NOT NULL;
