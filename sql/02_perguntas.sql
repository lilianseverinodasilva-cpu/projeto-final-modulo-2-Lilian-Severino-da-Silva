USE pncp_controladoria;

-- ============================================================================
-- PERGUNTA 1: Economia Global do Poder Público (Nominal e Percentual)
-- ============================================================================
SELECT 
    COUNT(*) AS total_itens_comparaveis,
    SUM(valor_total_estimado) AS total_estimado,
    SUM(valor_total_homologado) AS total_homologado,
    SUM(economia_valor) AS economia_nominal_R$,
    ROUND(100.0 * SUM(economia_valor) / SUM(valor_total_estimado), 2) AS percentual_economia
FROM fato_item_contratado
WHERE comparavel = 1;


USE pncp_controladoria;

-- ============================================================================
-- PERGUNTA 2: Concentração e Risco de Fornecedores (Top 10 + % do Orçamento)
-- ============================================================================
SELECT 
    forn.ni_fornecedor,
    forn.nome_fornecedor,
    SUM(f.valor_total_homologado) AS volume_homologado_R$,
    ROUND(
        100.0 * SUM(f.valor_total_homologado) / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 
        2
    ) AS pct_orcamento_global
FROM fato_item_contratado f
JOIN dim_fornecedor forn ON f.sk_fornecedor = forn.sk_fornecedor
GROUP BY forn.ni_fornecedor, forn.nome_fornecedor
ORDER BY volume_homologado_R$ DESC
LIMIT 10;

USE pncp_controladoria;

-- ============================================================================
-- PERGUNTA 3: Economia e Eficiência por Modalidade (Mais vs Menos Econômica)
-- ============================================================================
SELECT 
    m.nome_modalidade,
    COUNT(*) AS total_itens_comparaveis,
    SUM(f.valor_total_estimado) AS total_estimado_R$,
    SUM(f.valor_total_homologado) AS total_homologado_R$,
    SUM(f.economia_valor) AS economia_nominal_R$,
    ROUND(100.0 * SUM(f.economia_valor) / SUM(f.valor_total_estimado), 2) AS percentual_economia
FROM fato_item_contratado f
JOIN dim_modalidade m ON f.sk_modalidade = m.sk_modalidade
WHERE f.comparavel = 1
GROUP BY m.nome_modalidade
ORDER BY percentual_economia DESC;


USE pncp_controladoria;

-- ============================================================================
-- PERGUNTA 4: Tempo do Ciclo de Compras por Órgão Comprador (Top 10 Mais Lentos)
-- ============================================================================
SELECT 
    o.cnpj_orgao,
    o.nome_orgao,
    o.poder,
    COUNT(f.dias_ciclo) AS total_itens_com_ciclo,
    ROUND(AVG(f.dias_ciclo), 1) AS ciclo_medio_dias,
    MAX(f.dias_ciclo) AS ciclo_maximo_dias
FROM fato_item_contratado f
JOIN dim_orgao o ON f.sk_orgao = o.sk_orgao
WHERE f.dias_ciclo IS NOT NULL
GROUP BY o.cnpj_orgao, o.nome_orgao, o.poder
ORDER BY ciclo_medio_dias DESC
LIMIT 10;

USE pncp_controladoria;

-- Validação Global do Ciclo de Compras (Prova Real do Anexo 8)
SELECT 
    COUNT(dias_ciclo) AS itens_com_ciclo,
    ROUND(AVG(dias_ciclo), 1) AS ciclo_medio_dias,
    MAX(dias_ciclo) AS ciclo_maximo_dias
FROM fato_item_contratado
WHERE dias_ciclo IS NOT NULL;

-- ============================================================================
-- PERGUNTA 5: Distribuição Regional (Volume e % de Desconto por UF e Região)
-- ============================================================================

-- Visão por Região
SELECT 
    loc.regiao,
    COUNT(*) AS total_itens,
    SUM(f.valor_total_homologado) AS volume_homologado_R$,
    ROUND(100.0 * SUM(f.valor_total_homologado) / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2) AS pct_volume_global,
    ROUND(100.0 * SUM(CASE WHEN f.comparavel = 1 THEN f.economia_valor ELSE 0 END) / 
          NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS pct_desconto_medio
FROM fato_item_contratado f
JOIN dim_localidade loc ON f.sk_localidade = loc.sk_localidade
GROUP BY loc.regiao
ORDER BY volume_homologado_R$ DESC;

-- Visão por Estado (UF) - Top 10 em Volume e Desconto
SELECT 
    loc.uf_nome AS uf,
    loc.regiao,
    COUNT(*) AS total_itens,
    SUM(f.valor_total_homologado) AS volume_homologado_R$,
    ROUND(100.0 * SUM(CASE WHEN f.comparavel = 1 THEN f.economia_valor ELSE 0 END) / 
          NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS pct_desconto_medio
FROM fato_item_contratado f
JOIN dim_localidade loc ON f.sk_localidade = loc.sk_localidade
GROUP BY loc.uf_nome, loc.regiao
ORDER BY volume_homologado_R$ DESC;

-- ============================================================================
-- PERGUNTA 6: Perfil dos Gastos (Bens, Serviços, Obras e Engenharia)
-- ============================================================================
SELECT 
    f.perfil_gasto,
    COUNT(*) AS total_itens,
    SUM(f.valor_total_homologado) AS volume_homologado_R$,
    ROUND(100.0 * SUM(f.valor_total_homologado) / (SELECT SUM(valor_total_homologado) FROM fato_item_contratado), 2) AS pct_volume_homologado,
    SUM(CASE WHEN f.comparavel = 1 THEN f.economia_valor ELSE 0 END) AS economia_nominal_R$,
    ROUND(100.0 * SUM(CASE WHEN f.comparavel = 1 THEN f.economia_valor ELSE 0 END) / 
          NULLIF(SUM(CASE WHEN f.comparavel = 1 THEN f.valor_total_estimado ELSE 0 END), 0), 2) AS pct_economia_comparavel
FROM fato_item_contratado f
GROUP BY f.perfil_gasto
ORDER BY volume_homologado_R$ DESC;