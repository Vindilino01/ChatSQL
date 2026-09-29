CREATE TABLE categorias (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT
);

CREATE TABLE clientes (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT,
    cidade TEXT,
    estado TEXT,
    data_cadastro DATE
);

CREATE TABLE produtos (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    categoria_id INTEGER,
    preco REAL NOT NULL,
    estoque INTEGER,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

CREATE TABLE pedidos (
    id INTEGER PRIMARY KEY,
    cliente_id INTEGER NOT NULL,
    data_pedido DATE NOT NULL,
    status TEXT,
    valor_total REAL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE itens_pedido (
    id INTEGER PRIMARY KEY,
    pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL,
    preco_unitario REAL NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);
