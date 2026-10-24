-- sql/01_criar_banco.sql
-- DDL para a criacao do esquema Star Schema no MySQL

CREATE DATABASE IF NOT EXISTS pncp_controladoria;
USE pncp_controladoria;

-- Limpeza preventiva das tabelas caso existam (ordem respeita as restricoes de FK)
DROP TABLE IF EXISTS fato_item_contratado;
DROP TABLE IF EXISTS dim_orgao;
DROP TABLE IF EXISTS dim_fornecedor;
DROP TABLE IF EXISTS dim_modalidade;
DROP TABLE IF EXISTS dim_localidade;

-- -----------------------------------------------------------------------------
-- DIMENSOES
-- -----------------------------------------------------------------------------

-- 1. Dimensao Orgao (Quem comprou)
CREATE TABLE dim_orgao (
    sk_orgao INT INT AUTO_INCREMENT PRIMARY KEY, -- SK com sinal para aceitar a linha -1
    cnpj_orgao VARCHAR(14) UNIQUE,
    nome_orgao VARCHAR(255) NOT NULL,
    poder VARCHAR(50) NOT NULL
);

-- 2. Dimensao Fornecedor (Quem vendeu)
CREATE TABLE dim_fornecedor (
    sk_fornecedor INT AUTO_INCREMENT PRIMARY KEY,
    ni_fornecedor VARCHAR(20) UNIQUE,
    nome_fornecedor VARCHAR(255),
    tipo_pessoa VARCHAR(10),
    porte VARCHAR(50)
);

-- 3. Dimensao Modalidade (Como comprou)
CREATE TABLE dim_modalidade (
    sk_modalidade INT AUTO_INCREMENT PRIMARY KEY,
    modalidade_id INT UNIQUE NOT NULL,
    nome_modalidade VARCHAR(100) NOT NULL
);

-- 4. Dimensao Localidade (Onde)
CREATE TABLE dim_localidade (
    sk_localidade INT AUTO_INCREMENT PRIMARY KEY,
    uf_sigla VARCHAR(2) UNIQUE NOT NULL,
    uf_nome VARCHAR(100) NOT NULL,
    regiao VARCHAR(50) NOT NULL
);

-- -----------------------------------------------------------------------------
-- TABELA FATO (O que foi comprado)
-- -----------------------------------------------------------------------------
CREATE TABLE fato_item_contratado (
    sk_fato INT AUTO_INCREMENT PRIMARY KEY,
    numero_controle_pncp VARCHAR(50) NOT NULL,
    numero_item INT NOT NULL,
    
    -- Chaves Estrangeiras (FKs)
    sk_orgao INT NOT NULL,
    sk_fornecedor INT NOT NULL,
    sk_modalidade INT NOT NULL,
    sk_localidade INT NOT NULL,
    
    -- Datas
    data_publicacao DATE NOT NULL,
    data_homologacao DATE NULL, -- Nulo quando anulado pela regra de cronologia
    
    -- Atributos do Item
    descricao_item TEXT,
    perfil_gasto VARCHAR(50) NOT NULL,
    
    -- Metricas Numericas e Monetarias (DECIMAL para precisao)
    quantidade DECIMAL(18,4) NOT NULL,
    valor_unitario_estimado DECIMAL(18,4) NOT NULL,
    valor_total_estimado DECIMAL(18,2) NOT NULL,
    valor_unitario_homologado DECIMAL(18,4) NOT NULL,
    valor_total_homologado DECIMAL(18,2) NOT NULL,
    
    -- Colunas Calculadas
    comparavel TINYINT NOT NULL DEFAULT 1,
    economia_valor DECIMAL(18,2) NULL,
    dias_ciclo INT NULL,
    
    -- Restricao de Unicidade do Grao
    CONSTRAINT uk_item UNIQUE (numero_controle_pncp, numero_item),
    
    -- Integridade Referencial (FKs)
    CONSTRAINT fk_fato_orgao FOREIGN KEY (sk_orgao) REFERENCES dim_orgao(sk_orgao),
    CONSTRAINT fk_fato_fornecedor FOREIGN KEY (sk_fornecedor) REFERENCES dim_fornecedor(sk_fornecedor),
    CONSTRAINT fk_fato_modalidade FOREIGN KEY (sk_modalidade) REFERENCES dim_modalidade(sk_modalidade),
    CONSTRAINT fk_fato_localidade FOREIGN KEY (sk_localidade) REFERENCES dim_localidade(sk_localidade),
    
    -- Restricoes de Qualidade de Dados (CHECKs)
    CONSTRAINT chk_quantidade CHECK (quantidade > 0),
    CONSTRAINT chk_valores_positivos CHECK (valor_unitario_estimado >= 0 AND valor_unitario_homologado >= 0)
);