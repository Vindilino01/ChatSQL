CREATE TABLE regioes (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    uf TEXT
);

CREATE TABLE representantes (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT,
    regiao_id INTEGER,
    data_contratacao DATE,
    FOREIGN KEY (regiao_id) REFERENCES regioes(id)
);

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT,
    cidade TEXT,
    representante_id INTEGER,
    data_cadastro DATE,
    FOREIGN KEY (representante_id) REFERENCES representantes(id)
);

CREATE TABLE produtos (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    categoria TEXT
);

CREATE TABLE vendas (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    representante_id INTEGER,
    data_venda DATE NOT NULL,
    quantidade INTEGER NOT NULL,
    valor_total REAL NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id),
    FOREIGN KEY (representante_id) REFERENCES representantes(id)
);

CREATE TABLE metas (
    id INTEGER PRIMARY KEY,
    representante_id INTEGER NOT NULL,
    mes DATE,
    valor_meta REAL,
    FOREIGN KEY (representante_id) REFERENCES representantes(id)
);
