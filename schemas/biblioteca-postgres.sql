-- ============================================================
-- BANCO DE DADOS: BIBLIOTECA UNIVERSITARIA
-- SGBD: PostgreSQL 14+ (testado no PostgreSQL 18 / Neon)
-- Schema: public
--
-- Este arquivo cria apenas a ESTRUTURA (tabelas, restricoes e indices).
-- Os dados ficticios ficam em scripts/seed_biblioteca.py.
--
-- Como aplicar:
--   1) Neon: cole este arquivo no SQL Editor.
--   2) Local/CI: python scripts/apply_ddl.py
-- ============================================================

-- Extensao usada pelo indice de busca por trecho no titulo.
-- Se o usuario nao puder criar extensoes, remova as duas linhas do indice
-- idx_livro_titulo_trgm (a busca por trecho continua funcionando, so mais lenta).
CREATE EXTENSION IF NOT EXISTS pg_trgm;


-- ------------------------------------------------------------
-- 1. USUARIO
-- ------------------------------------------------------------
CREATE TABLE usuario (
    id_usuario    BIGINT GENERATED ALWAYS AS IDENTITY,
    nome          VARCHAR(120) NOT NULL,
    documento     VARCHAR(11)  NOT NULL,
    email         VARCHAR(150) NOT NULL,
    tipo_usuario  VARCHAR(20)  NOT NULL,
    data_cadastro TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT pk_usuario
        PRIMARY KEY (id_usuario),

    CONSTRAINT uk_usuario_documento
        UNIQUE (documento),

    CONSTRAINT uk_usuario_email
        UNIQUE (email),

    CONSTRAINT ck_usuario_tipo
        CHECK (tipo_usuario IN ('aluno', 'professor', 'funcionario')),

    -- CPF guardado apenas com os 11 digitos (sem pontos e traco).
    -- Armazenar formatado quebraria a unicidade: "123.456.789-01" e
    -- "12345678901" seriam strings diferentes para o banco.
    CONSTRAINT ck_usuario_documento
        CHECK (documento ~ '^[0-9]{11}$')
);


-- ------------------------------------------------------------
-- 2. EDITORA
-- ------------------------------------------------------------
CREATE TABLE editora (
    id_editora BIGINT GENERATED ALWAYS AS IDENTITY,
    nome       VARCHAR(120) NOT NULL,
    pais       VARCHAR(60)  NOT NULL,

    CONSTRAINT pk_editora
        PRIMARY KEY (id_editora),

    CONSTRAINT uk_editora_nome
        UNIQUE (nome)
);


-- ------------------------------------------------------------
-- 3. AUTOR
-- ------------------------------------------------------------
CREATE TABLE autor (
    id_autor      BIGINT GENERATED ALWAYS AS IDENTITY,
    nome          VARCHAR(120) NOT NULL,
    nacionalidade VARCHAR(60),

    CONSTRAINT pk_autor
        PRIMARY KEY (id_autor)
);


-- ------------------------------------------------------------
-- 4. LIVRO
-- ------------------------------------------------------------
CREATE TABLE livro (
    id_livro       BIGINT GENERATED ALWAYS AS IDENTITY,
    titulo         VARCHAR(200) NOT NULL,
    isbn           VARCHAR(13)  NOT NULL,
    ano_publicacao SMALLINT     NOT NULL,
    id_editora     BIGINT       NOT NULL,

    CONSTRAINT pk_livro
        PRIMARY KEY (id_livro),

    CONSTRAINT uk_livro_isbn
        UNIQUE (isbn),

    -- ISBN-13 apenas com digitos, pelo mesmo motivo do CPF.
    CONSTRAINT ck_livro_isbn
        CHECK (isbn ~ '^[0-9]{13}$'),

    -- "> 0" aceitaria o ano 30000; a faixa mantem dados plausiveis.
    CONSTRAINT ck_livro_ano
        CHECK (ano_publicacao BETWEEN 1400 AND 2100),

    CONSTRAINT fk_livro_editora
        FOREIGN KEY (id_editora)
        REFERENCES editora (id_editora)
        ON DELETE RESTRICT
);

CREATE INDEX idx_livro_editora ON livro (id_editora);

-- Indice para busca por trecho ("livros que contem 'dom'"), que e o tipo de
-- filtro que o Chat SQL gera. Um indice btree comum NAO atende LIKE '%...%'.
CREATE INDEX idx_livro_titulo_trgm ON livro USING gin (titulo gin_trgm_ops);


-- ------------------------------------------------------------
-- 5. EXEMPLAR
-- ------------------------------------------------------------
CREATE TABLE exemplar (
    id_exemplar        BIGINT GENERATED ALWAYS AS IDENTITY,
    codigo_patrimonio  VARCHAR(30) NOT NULL,
    id_livro           BIGINT      NOT NULL,
    estado_conservacao VARCHAR(20) NOT NULL,

    CONSTRAINT pk_exemplar
        PRIMARY KEY (id_exemplar),

    CONSTRAINT uk_exemplar_patrimonio
        UNIQUE (codigo_patrimonio),

    CONSTRAINT fk_exemplar_livro
        FOREIGN KEY (id_livro)
        REFERENCES livro (id_livro)
        ON DELETE RESTRICT,

    CONSTRAINT ck_exemplar_estado
        CHECK (
            estado_conservacao IN (
                'bom',
                'danificado',
                'em_manutencao',
                'extraviado',
                'descartado'
            )
        )
);

CREATE INDEX idx_exemplar_livro ON exemplar (id_livro);


-- ------------------------------------------------------------
-- 6. LIVRO_AUTOR (relacao N:N entre livro e autor)
-- ------------------------------------------------------------
CREATE TABLE livro_autor (
    id_livro BIGINT NOT NULL,
    id_autor BIGINT NOT NULL,

    CONSTRAINT pk_livro_autor
        PRIMARY KEY (id_livro, id_autor),

    -- CASCADE aqui e proposital: sem o livro, a ligacao livro-autor nao faz
    -- sentido. Nas demais FKs usamos RESTRICT para nao apagar historico.
    CONSTRAINT fk_livro_autor_livro
        FOREIGN KEY (id_livro)
        REFERENCES livro (id_livro)
        ON DELETE CASCADE,

    CONSTRAINT fk_livro_autor_autor
        FOREIGN KEY (id_autor)
        REFERENCES autor (id_autor)
        ON DELETE RESTRICT
);

CREATE INDEX idx_livro_autor_autor ON livro_autor (id_autor);


-- ------------------------------------------------------------
-- 7. EMPRESTIMO
-- ------------------------------------------------------------
CREATE TABLE emprestimo (
    id_emprestimo           BIGINT GENERATED ALWAYS AS IDENTITY,
    id_usuario              BIGINT NOT NULL,
    id_exemplar             BIGINT NOT NULL,
    data_emprestimo         DATE   NOT NULL DEFAULT CURRENT_DATE,
    data_prevista_devolucao DATE   NOT NULL,
    data_devolucao          DATE,

    CONSTRAINT pk_emprestimo
        PRIMARY KEY (id_emprestimo),

    CONSTRAINT fk_emprestimo_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario)
        ON DELETE RESTRICT,

    CONSTRAINT fk_emprestimo_exemplar
        FOREIGN KEY (id_exemplar)
        REFERENCES exemplar (id_exemplar)
        ON DELETE RESTRICT,

    -- A devolucao prevista tem de ser POSTERIOR ao emprestimo (no mesmo dia
    -- nao faz sentido) e a devolucao real nao pode ser anterior a retirada.
    CONSTRAINT ck_emprestimo_datas
        CHECK (
            data_prevista_devolucao > data_emprestimo
            AND (
                data_devolucao IS NULL
                OR data_devolucao >= data_emprestimo
            )
        )
);

CREATE INDEX idx_emprestimo_usuario ON emprestimo (id_usuario);
CREATE INDEX idx_emprestimo_exemplar ON emprestimo (id_exemplar);
CREATE INDEX idx_emprestimo_data ON emprestimo (data_emprestimo);

-- Regra de negocio no banco: um exemplar nao pode ter dois emprestimos
-- abertos (sem devolucao) ao mesmo tempo.
CREATE UNIQUE INDEX idx_exemplar_emprestimo_ativo
    ON emprestimo (id_exemplar)
    WHERE data_devolucao IS NULL;


-- ------------------------------------------------------------
-- Estatisticas para o planejador de consultas
-- ------------------------------------------------------------
ANALYZE;
