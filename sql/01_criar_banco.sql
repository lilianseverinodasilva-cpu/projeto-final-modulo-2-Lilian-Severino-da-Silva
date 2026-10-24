CREATE DATABASE IF NOT EXISTS pncp_controladoria;
USE pncp_controladoria;

-- 1. Dimensão Órgão
CREATE TABLE IF NOT EXISTS dim_orgao (
    sk_orgao INT AUTO_INCREMENT PRIMARY KEY,
    cnpj_orgao VARCHAR(14) UNIQUE,
    nome_orgao VARCHAR(255),
    poder VARCHAR(50)
);

-- 2. Dimensão Fornecedor
CREATE TABLE IF NOT EXISTS dim_fornecedor (
    sk_fornecedor INT AUTO_INCREMENT PRIMARY KEY,
    ni_fornecedor VARCHAR(20) UNIQUE,
    nome_fornecedor VARCHAR(255),
    tipo_pessoa VARCHAR(10),
    porte VARCHAR(50)
);

-- 3. Dimensão Modalidade
CREATE TABLE IF NOT EXISTS dim_modalidade (
    sk_modalidade INT AUTO_INCREMENT PRIMARY KEY,
    modalidade_id INT UNIQUE,
    nome_modalidade VARCHAR(100)
);

-- 4. Dimensão Localidade
CREATE TABLE IF NOT EXISTS dim_localidade (
    sk_localidade INT AUTO_INCREMENT PRIMARY KEY,
    uf_sigla VARCHAR(2) UNIQUE,
    uf_nome VARCHAR(50),
    regiao VARCHAR(50)
);

-- 5. Tabela Fato: Item Contratado
CREATE TABLE IF NOT EXISTS fato_item_contratado (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_controle_pncp VARCHAR(100),
    numero_item INT,
    sk_orgao INT,
    sk_fornecedor INT,
    sk_modalidade INT,
    sk_localidade INT,
    data_publicacao DATE,
    data_homologacao DATE,
    descricao_item TEXT,
    perfil_gasto VARCHAR(50),
    quantidade DECIMAL(15,4),
    valor_unitario_estimado DECIMAL(15,2),
    valor_total_estimado DECIMAL(15,2),
    valor_unitario_homologado DECIMAL(15,2),
    valor_total_homologado DECIMAL(15,2),
    comparavel INT,
    economia_valor DECIMAL(15,2),
    dias_ciclo INT,
    CONSTRAINT fk_orgao FOREIGN KEY (sk_orgao) REFERENCES dim_orgao(sk_orgao),
    CONSTRAINT fk_fornecedor FOREIGN KEY (sk_fornecedor) REFERENCES dim_fornecedor(sk_fornecedor),
    CONSTRAINT fk_modalidade FOREIGN KEY (sk_modalidade) REFERENCES dim_modalidade(sk_modalidade),
    CONSTRAINT fk_localidade FOREIGN KEY (sk_localidade) REFERENCES dim_localidade(sk_localidade)
);