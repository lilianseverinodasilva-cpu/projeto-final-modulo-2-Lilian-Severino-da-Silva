"""
montar_tabelas.py - MONTAGEM DAS TABELAS DIMENSIONAIS E FATO (Sprint 3)
====================================================================
"""

import re
import pandas as pd
from src import config, limpeza


def ler(nome, **opcoes):
    """Lê um CSV da pasta data/raw/ como string pura (dtype=str)."""
    return pd.read_csv(config.PASTA_RAW / f"{nome}.csv", dtype=str, keep_default_na=False, **opcoes)


def salvar(df, nome):
    """Salva um DataFrame na pasta data/processed/ em formato CSV."""
    df.to_csv(config.PASTA_PROCESSED / f"{nome}.csv", index=False)
    print(f"   {nome}.csv: {len(df)} linhas salvas em data/processed/")


def main():
    print("=== SPRINT 3: PROCESSAMENTO E MONTAGEM DAS TABELAS ===")

    # 1. Leitura dos dados brutos
    compras = ler("compras")
    itens = ler("itens")
    resultados = ler("resultados")

    # Mapeamento dinâmico de colunas nos arquivos brutos antes do merge
    for col in itens.columns:
        c_lower = col.lower().strip()
        if c_lower in ["valor_total", "valor_estimado_total", "valor_total_estimado", "valor_estimado"]:
            itens = itens.rename(columns={col: "valor_total_estimado"})
        elif c_lower in ["valor_unitario", "valor_estimado_unitario", "valor_unitario_estimado"]:
            itens = itens.rename(columns={col: "valor_unitario_estimado"})
        elif c_lower in ["sigilo", "orcamento_sigiloso", "item_sigiloso", "indicador_sigilo"]:
            itens = itens.rename(columns={col: "orcamento_sigiloso"})

    for col in resultados.columns:
        c_lower = col.lower().strip()
        if c_lower in ["valor_total", "valor_homologado", "valor_total_homologado", "valor_homologado_total"]:
            resultados = resultados.rename(columns={col: "valor_total_homologado"})
        elif c_lower in ["valor_unitario", "valor_unitario_homologado"]:
            resultados = resultados.rename(columns={col: "valor_unitario_homologado"})

    # 2. Filtragem de resultados ativos (descarrega cancelados)
    res_validos = resultados[resultados["data_cancelamento"].str.strip() == ""].copy()

    # Seleção do 1º colocado no SRP
    res_validos["ordem_srp"] = res_validos["ordem_classificacao_srp"].apply(limpeza.converter_numero)
    res_validos["seq_res"] = res_validos["sequencial_resultado"].apply(limpeza.converter_numero)
    res_validos = res_validos.sort_values(by=["numero_controle_pncp", "numero_item", "ordem_srp", "seq_res"])
    vencedores = res_validos.drop_duplicates(subset=["numero_controle_pncp", "numero_item"], keep="first").copy()

    # 3. Junção (Merge) com sufixos explícitos
    itens_vencedores = itens.merge(vencedores, on=["numero_controle_pncp", "numero_item"], how="inner", suffixes=("_item", "_res"))
    df_base = itens_vencedores.merge(compras, on="numero_controle_pncp", how="inner")

    # Resolução unificada de colunas de valores pós-merge
    def obter_coluna(df, lista_opcoes):
        for op in lista_opcoes:
            if op in df.columns:
                return df[op]
        return pd.Series("", index=df.index)

    col_v_tot_est = obter_coluna(df_base, ["valor_total_estimado", "valor_total_estimado_item", "valor_total_x", "valor_total"])
    col_v_tot_hom = obter_coluna(df_base, ["valor_total_homologado", "valor_total_homologado_res", "valor_total_y", "valor_homologado"])
    col_v_unit_est = obter_coluna(df_base, ["valor_unitario_estimado", "valor_unitario_estimado_item", "valor_unitario_x", "valor_unitario"])
    col_v_unit_hom = obter_coluna(df_base, ["valor_unitario_homologado", "valor_unitario_homologado_res", "valor_unitario_y"])

    # 4. Aplicação das funções de limpeza usando as séries resolvidas
    df_base["qtd"] = df_base["quantidade"].apply(limpeza.converter_numero)
    df_base["v_unit_est"] = col_v_unit_est.apply(limpeza.converter_numero)
    df_base["v_tot_est"] = col_v_tot_est.apply(limpeza.converter_numero)
    df_base["v_unit_hom"] = col_v_unit_hom.apply(limpeza.converter_numero)
    df_base["v_tot_hom"] = col_v_tot_hom.apply(limpeza.converter_numero)

    # Recalcula totais caso estejam zerados ou ausentes
    df_base["v_tot_est"] = df_base.apply(
        lambda r: r["qtd"] * r["v_unit_est"] if (r["v_tot_est"] == 0 or pd.isna(r["v_tot_est"])) else r["v_tot_est"], axis=1
    )
    df_base["v_tot_hom"] = df_base.apply(
        lambda r: r["qtd"] * r["v_unit_hom"] if (r["v_tot_hom"] == 0 or pd.isna(r["v_tot_hom"])) else r["v_tot_hom"], axis=1
    )

    # 5. Regra 4: Filtro de Itens Rejeitados (Inválidos)
    col_sigilo = None
    for c in ["orcamento_sigiloso", "sigilo", "item_sigiloso", "indicador_sigilo", "orcamento_sigiloso_item"]:
        if c in df_base.columns:
            col_sigilo = c
            break

    if col_sigilo:
        sigiloso = df_base[col_sigilo].astype(str).str.upper().str.strip().isin(["1", "SIM", "TRUE", "S"])
    else:
        sigiloso = pd.Series(False, index=df_base.index)
    
    rejeitado = (
        (df_base["qtd"] <= 0) |
        (df_base["v_unit_est"] <= 0) |
        (df_base["v_unit_hom"] <= 0) |
        (df_base["v_tot_est"] < 1.0) |
        sigiloso |
        (df_base["v_tot_hom"] > df_base["v_tot_est"] * 1000) |
        (df_base["v_tot_est"] > 1e12) |
        (df_base["v_tot_hom"] > 1e12)
    )

    fato = df_base[~rejeitado].copy()

    # 6. Regra 6: Comparabilidade e Economia
    modalidade_id = fato["modalidade_id"].apply(limpeza.converter_numero).astype(int)
    razao = fato["v_tot_hom"] / fato["v_tot_est"]
    
    fato["comparavel"] = ((modalidade_id != 12) & (razao >= 0.1) & (razao <= 10.0)).astype(int)
    fato["economia_valor"] = fato.apply(
        lambda r: (r["v_tot_est"] - r["v_tot_hom"]) if r["comparavel"] == 1 else None, axis=1
    )

    # 7. Regra 7: Tratamento de Datas e Ciclo
    fato["dt_pub"] = fato["data_publicacao"].apply(limpeza.converter_data)
    fato["dt_hom"] = fato["data_resultado"].apply(limpeza.converter_data)

    def calc_ciclo(r):
        if pd.isna(r["dt_pub"]) or pd.isna(r["dt_hom"]):
            return None, None
        p = pd.to_datetime(r["dt_pub"])
        h = pd.to_datetime(r["dt_hom"])
        dias = (h - p).days
        if dias < 0:
            return None, None
        return r["dt_hom"], dias

    res_datas = fato.apply(calc_ciclo, axis=1)
    fato["data_homologacao"] = [d[0] for d in res_datas]
    fato["dias_ciclo"] = [d[1] for d in res_datas]
    fato["data_publicacao"] = fato["dt_pub"]

    # 8. Regra 8: Perfil do Gasto
    regex_obras = re.compile(r"\b(?:OBRAS?|CONSTRUÇÃO|CONSTRUCAO|REFORMA|ENGENHARIA)\b", re.IGNORECASE)
    regex_servicos = re.compile(r"\b(?:SERVIÇOS?|SERVICOS?|MANUTENÇÃO|MANUTENCAO|CONSULTORIA|LOCAÇÃO|LOCACAO|TREINAMENTO)\b", re.IGNORECASE)

    def classificar_perfil(r):
        texto = f"{r['objeto_compra']} {r['descricao']}"
        if regex_obras.search(texto):
            return "Obras e engenharia"
        elif regex_servicos.search(texto):
            return "Serviços"
        return "Bens"

    fato["perfil_gasto"] = fato.apply(classificar_perfil, axis=1)
    fato["descricao_item"] = fato["descricao"].apply(limpeza.limpar_texto)

    # 9. Construção das Tabelas Dimensionais
    dim_orgao = fato[["cnpj_orgao", "razao_social_orgao", "poder_id"]].drop_duplicates().copy()
    dim_orgao["cnpj_orgao"] = dim_orgao["cnpj_orgao"].apply(lambda x: limpeza.limpar_documento(x, "PJ"))
    dim_orgao["nome_orgao"] = dim_orgao["razao_social_orgao"].apply(limpeza.padronizar_nome)
    
    mapa_poder = {"1": "Executivo", "2": "Legislativo", "3": "Judiciario"}
    dim_orgao["poder"] = dim_orgao["poder_id"].astype(str).map(lambda p: mapa_poder.get(p, "Executivo"))
    dim_orgao = dim_orgao.drop_duplicates(subset=["cnpj_orgao"]).reset_index(drop=True)
    dim_orgao["sk_orgao"] = dim_orgao.index + 1
    dim_orgao = dim_orgao[["sk_orgao", "cnpj_orgao", "nome_orgao", "poder"]]

    dim_fornec = fato[["ni_fornecedor", "nome_fornecedor", "tipo_pessoa", "porte"]].drop_duplicates().copy()
    dim_fornec["tipo_pessoa"] = dim_fornec["tipo_pessoa"].astype(str).str.upper().str.strip()
    dim_fornec["ni_fornecedor"] = dim_fornec.apply(lambda r: limpeza.limpar_documento(r["ni_fornecedor"], r["tipo_pessoa"]), axis=1)
    dim_fornec["nome_fornecedor"] = dim_fornec["nome_fornecedor"].apply(limpeza.padronizar_nome)
    dim_fornec["porte"] = dim_fornec["porte"].apply(limpeza.limpar_texto)
    dim_fornec = dim_fornec.drop_duplicates(subset=["ni_fornecedor"]).reset_index(drop=True)
    dim_fornec["sk_fornecedor"] = dim_fornec.index + 1
    dim_fornec = dim_fornec[["sk_fornecedor", "ni_fornecedor", "nome_fornecedor", "tipo_pessoa", "porte"]]

    dim_mod = fato[["modalidade_id", "modalidade_nome"]].drop_duplicates().copy()
    dim_mod["modalidade_id"] = dim_mod["modalidade_id"].apply(limpeza.converter_numero).astype(int)
    dim_mod["nome_modalidade"] = dim_mod["modalidade_nome"].apply(limpeza.padronizar_nome)
    dim_mod = dim_mod.drop_duplicates(subset=["modalidade_id"]).sort_values("modalidade_id").reset_index(drop=True)
    dim_mod["sk_modalidade"] = dim_mod.index + 1
    dim_mod = dim_mod[["sk_modalidade", "modalidade_id", "nome_modalidade"]]

    mapa_regiao = {
        'AC': 'Norte', 'AL': 'Nordeste', 'AP': 'Norte', 'AM': 'Norte', 'BA': 'Nordeste',
        'CE': 'Nordeste', 'DF': 'Centro-Oeste', 'ES': 'Sudeste', 'GO': 'Centro-Oeste',
        'MA': 'Nordeste', 'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste', 'MG': 'Sudeste',
        'PA': 'Norte', 'PB': 'Nordeste', 'PR': 'Sul', 'PE': 'Nordeste', 'PI': 'Nordeste',
        'RJ': 'Sudeste', 'RN': 'Nordeste', 'RS': 'Sul', 'RO': 'Norte', 'RR': 'Norte',
        'SC': 'Sul', 'SP': 'Sudeste', 'SE': 'Nordeste', 'TO': 'Norte'
    }
    mapa_uf = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapa', 'AM': 'Amazonas', 'BA': 'Bahia',
        'CE': 'Ceara', 'DF': 'Distrito Federal', 'ES': 'Espirito Santo', 'GO': 'Goias',
        'MA': 'Maranhao', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
        'PA': 'Para', 'PB': 'Paraiba', 'PR': 'Parana', 'PE': 'Pernambuco', 'PI': 'Piaui',
        'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul',
        'RO': 'Rondonia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'Sao Paulo',
        'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    dim_loc = fato[["uf_sigla"]].drop_duplicates().copy()
    dim_loc["uf_sigla"] = dim_loc["uf_sigla"].astype(str).str.upper().str.strip()
    dim_loc["uf_nome"] = dim_loc["uf_sigla"].map(lambda u: mapa_uf.get(u, u))
    dim_loc["regiao"] = dim_loc["uf_sigla"].map(lambda u: mapa_regiao.get(u, "Outros"))
    dim_loc = dim_loc.drop_duplicates(subset=["uf_sigla"]).sort_values("uf_sigla").reset_index(drop=True)
    dim_loc["sk_localidade"] = dim_loc.index + 1
    dim_loc = dim_loc[["sk_localidade", "uf_sigla", "uf_nome", "regiao"]]

    # 10. Mapeamento das SKs na Tabela Fato
    fato["cnpj_orgao"] = fato["cnpj_orgao"].apply(lambda x: limpeza.limpar_documento(x, "PJ"))
    fato["ni_fornecedor"] = fato.apply(lambda r: limpeza.limpar_documento(r["ni_fornecedor"], r["tipo_pessoa"]), axis=1)
    fato["modalidade_id"] = fato["modalidade_id"].apply(limpeza.converter_numero).astype(int)
    fato["uf_sigla"] = fato["uf_sigla"].astype(str).str.upper().str.strip()

    fato = fato.merge(dim_orgao[["cnpj_orgao", "sk_orgao"]], on="cnpj_orgao", how="left")
    fato = fato.merge(dim_fornec[["ni_fornecedor", "sk_fornecedor"]], on="ni_fornecedor", how="left")
    fato = fato.merge(dim_mod[["modalidade_id", "sk_modalidade"]], on="modalidade_id", how="left")
    fato = fato.merge(dim_loc[["uf_sigla", "sk_localidade"]], on="uf_sigla", how="left")

    colunas_fato = [
        "numero_controle_pncp", "numero_item", "sk_orgao", "sk_fornecedor",
        "sk_modalidade", "sk_localidade", "data_publicacao", "data_homologacao",
        "descricao_item", "perfil_gasto", "quantidade", "v_unit_est",
        "v_tot_est", "v_unit_hom", "v_tot_hom", "comparavel",
        "economia_valor", "dias_ciclo"
    ]
    
    fato_final = fato[colunas_fato].copy()
    fato_final.columns = [
        "numero_controle_pncp", "numero_item", "sk_orgao", "sk_fornecedor",
        "sk_modalidade", "sk_localidade", "data_publicacao", "data_homologacao",
        "descricao_item", "perfil_gasto", "quantidade", "valor_unitario_estimado",
        "valor_total_estimado", "valor_unitario_homologado", "valor_total_homologado",
        "comparavel", "economia_valor", "dias_ciclo"
    ]

    # 11. Salvando arquivos em data/processed/
    salvar(dim_orgao, "dim_orgao")
    salvar(dim_fornec, "dim_fornecedor")
    salvar(dim_mod, "dim_modalidade")
    salvar(dim_loc, "dim_localidade")
    salvar(fato_final, "fato_item_contratado")

    print("\n=== CONFERENCIA dos resultados gerados ===")
    print(f"Itens na Fato: {len(fato_final)}")
    print(f"Volume Homologado Total: R$ {fato_final['valor_total_homologado'].sum():,.2f}")
    print(f"Economia Nominal: R$ {fato_final['economia_valor'].sum():,.2f}")


if __name__ == "__main__":
    main()