CREATE TABLE departamentos (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    localizacao TEXT
);

CREATE TABLE cargos (
    id INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL,
    salario_base REAL,
    departamento_id INTEGER,
    FOREIGN KEY (departamento_id) REFERENCES departamentos(id)
);

CREATE TABLE funcionarios (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT,
    cargo_id INTEGER,
    data_admissao DATE,
    ativo BOOLEAN,
    FOREIGN KEY (cargo_id) REFERENCES cargos(id)
);

CREATE TABLE avaliacoes_desempenho (
    id INTEGER PRIMARY KEY,
    funcionario_id INTEGER NOT NULL,
    data_avaliacao DATE,
    nota REAL,
    comentario TEXT,
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
);
