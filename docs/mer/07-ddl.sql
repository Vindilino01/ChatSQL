-- ============================================================
-- BANCO DE DADOS: BIBLIOTECA UNIVERSITARIA
-- Gerado automaticamente a partir do banco em uso.
-- Fonte: information_schema / pg_catalog (PostgreSQL).
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE "autor" (
    "id_autor" BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    "nome" CHARACTER VARYING(120) NOT NULL,
    "nacionalidade" CHARACTER VARYING(60),
    CONSTRAINT pk_autor PRIMARY KEY ("id_autor")
);


CREATE TABLE "editora" (
    "id_editora" BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    "nome" CHARACTER VARYING(120) NOT NULL,
    "pais" CHARACTER VARYING(60) NOT NULL,
    CONSTRAINT pk_editora PRIMARY KEY ("id_editora"),
    CONSTRAINT uk_editora_nome UNIQUE ("nome")
);


CREATE TABLE "livro" (
    "id_livro" BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    "titulo" CHARACTER VARYING(200) NOT NULL,
    "isbn" CHARACTER VARYING(13) NOT NULL,
    "ano_publicacao" SMALLINT NOT NULL,
    "id_editora" BIGINT NOT NULL,
    CONSTRAINT pk_livro PRIMARY KEY ("id_livro"),
    CONSTRAINT uk_livro_isbn UNIQUE ("isbn"),
    CONSTRAINT ck_livro_ano CHECK (((ano_publicacao >= 1400) AND (ano_publicacao <= 2100))),
    CONSTRAINT ck_livro_isbn CHECK (((isbn)::text ~ '^[0-9]{13}$'::text)),
    CONSTRAINT fk_livro_id_editora
        FOREIGN KEY ("id_editora") REFERENCES "editora" ("id_editora")
        ON DELETE RESTRICT
);


CREATE TABLE "exemplar" (
    "id_exemplar" BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    "codigo_patrimonio" CHARACTER VARYING(30) NOT NULL,
    "id_livro" BIGINT NOT NULL,
    "estado_conservacao" CHARACTER VARYING(20) NOT NULL,
    CONSTRAINT pk_exemplar PRIMARY KEY ("id_exemplar"),
    CONSTRAINT uk_exemplar_patrimonio UNIQUE ("codigo_patrimonio"),
    CONSTRAINT ck_exemplar_estado CHECK (((estado_conservacao)::text = ANY ((ARRAY['bom'::character varying, 'danificado'::character varying, 'em_manutencao'::character varying, 'extraviado'::character varying, 'descartado'::character varying])::text[]))),
    CONSTRAINT fk_exemplar_id_livro
        FOREIGN KEY ("id_livro") REFERENCES "livro" ("id_livro")
        ON DELETE RESTRICT
);


CREATE TABLE "usuario" (
    "id_usuario" BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    "nome" CHARACTER VARYING(120) NOT NULL,
    "documento" CHARACTER VARYING(11) NOT NULL,
    "email" CHARACTER VARYING(150) NOT NULL,
    "tipo_usuario" CHARACTER VARYING(20) NOT NULL,
    "data_cadastro" TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    CONSTRAINT pk_usuario PRIMARY KEY ("id_usuario"),
    CONSTRAINT uk_usuario_documento UNIQUE ("documento"),
    CONSTRAINT uk_usuario_email UNIQUE ("email"),
    CONSTRAINT ck_usuario_documento CHECK (((documento)::text ~ '^[0-9]{11}$'::text)),
    CONSTRAINT ck_usuario_tipo CHECK (((tipo_usuario)::text = ANY ((ARRAY['aluno'::character varying, 'professor'::character varying, 'funcionario'::character varying])::text[])))
);


CREATE TABLE "emprestimo" (
    "id_emprestimo" BIGINT GENERATED ALWAYS AS IDENTITY NOT NULL,
    "id_usuario" BIGINT NOT NULL,
    "id_exemplar" BIGINT NOT NULL,
    "data_emprestimo" DATE DEFAULT CURRENT_DATE NOT NULL,
    "data_prevista_devolucao" DATE NOT NULL,
    "data_devolucao" DATE,
    CONSTRAINT pk_emprestimo PRIMARY KEY ("id_emprestimo"),
    CONSTRAINT ck_emprestimo_datas CHECK (((data_prevista_devolucao > data_emprestimo) AND ((data_devolucao IS NULL) OR (data_devolucao >= data_emprestimo)))),
    CONSTRAINT fk_emprestimo_id_exemplar
        FOREIGN KEY ("id_exemplar") REFERENCES "exemplar" ("id_exemplar")
        ON DELETE RESTRICT,
    CONSTRAINT fk_emprestimo_id_usuario
        FOREIGN KEY ("id_usuario") REFERENCES "usuario" ("id_usuario")
        ON DELETE RESTRICT
);


CREATE TABLE "livro_autor" (
    "id_livro" BIGINT NOT NULL,
    "id_autor" BIGINT NOT NULL,
    CONSTRAINT pk_livro_autor PRIMARY KEY ("id_livro", "id_autor"),
    CONSTRAINT fk_livro_autor_id_autor
        FOREIGN KEY ("id_autor") REFERENCES "autor" ("id_autor")
        ON DELETE RESTRICT,
    CONSTRAINT fk_livro_autor_id_livro
        FOREIGN KEY ("id_livro") REFERENCES "livro" ("id_livro")
        ON DELETE CASCADE
);


-- Índices
CREATE INDEX idx_emprestimo_data ON public.emprestimo USING btree (data_emprestimo);
CREATE INDEX idx_emprestimo_exemplar ON public.emprestimo USING btree (id_exemplar);
CREATE INDEX idx_emprestimo_usuario ON public.emprestimo USING btree (id_usuario);
CREATE INDEX idx_exemplar_livro ON public.exemplar USING btree (id_livro);
CREATE INDEX idx_livro_editora ON public.livro USING btree (id_editora);
CREATE INDEX idx_livro_titulo_trgm ON public.livro USING gin (titulo gin_trgm_ops);
CREATE INDEX idx_livro_autor_autor ON public.livro_autor USING btree (id_autor);

-- Índice único parcial: impede dois empréstimos abertos no mesmo exemplar
CREATE UNIQUE INDEX idx_exemplar_emprestimo_ativo ON public.emprestimo USING btree (id_exemplar) WHERE (data_devolucao IS NULL);
