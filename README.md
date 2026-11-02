# Esteira Analítica de Compras Públicas PNCP - Controladoria Geral

## Índice

1. [Contextualização do Projeto](#1-contextualizacao-do-projeto)

2. [Arquitetura da Solução e Estrutura de Pastas](#2-arquitetura-da-solucao-e-estrutura-de-pastas)

3. [Dicionário dos Dados Brutos](#3-dicionario-dos-dados-brutos)

4. [Desenvolvimento do Projeto e Rastreabilidade por Sprints](#4-desenvolvimento-do-projeto-e-rastreabilidade-por-sprints)

   * 4.1. [Sprint 0: Planejamento, Arquitetura e Configuração](#41-sprint-0-planejamento-arquitetura-e-configuracao)

   * 4.2. [Sprint 1 & 2: Auditoria e Sanitização de Dados (EDA & Engenharia)](#42-sprint-1--2-auditoria-e-sanitizacao-de-dados-eda--engenharia)

   * 4.3. [Sprint 3: Regras de Negócio e Montagem do Star Schema (ETL)](#43-sprint-3-regras-de-negocio-e-montagem-do-star-schema-etl)

   * 4.4. [Sprint 4: Carga Automatizada e DW Relacional no MySQL](#44-sprint-4-carga-automatizada-e-dw-relacional-no-mysql)

   * 4.5. [Sprint 5: Consultas Analíticas e Perguntas de Negócio (SQL)](#45-sprint-5-consultas-analiticas-e-perguntas-de-negocio-sql)

   * 4.6. [Sprint 6: Relatório Executivo e Dashboard no Power BI](#46-sprint-6-relatorio-executivo-e-dashboard-no-power-bi)

5. [Desafios Técnicos Superados Durante a Execução](#47-desafios-tecnicos-superados-durante-a-execucao)

6. [Prova Real e Validação de Resultados](#48-prova-real-e-validacao-de-resultados)

7. [Instruções de Reprodução e Execução](#5-instrucoes-de-reproducao-e-execucao)


---
## 1. Contextualização do Projeto

Este projeto constrói uma esteira analítica ponta a ponta (End-to-End) para auditar, sanitizar, modelar e visualizar dados brutos de contratações públicas federais extraídos do Portal Nacional de Contratações Públicas (PNCP) referentes a 2025. O objetivo é fornecer subsídios técnicos para órgãos de controle na identificação de gargalos operacionais, indícios de sobrepreço, concentração atípica de contratos, morosidade licitatória e baixa competitividade.

---
## 2. Arquitetura da Solução e Estrutura de Pastas

A esteira integra scripts de ETL em Python, Data Warehouse (Star Schema) no MySQL e relatório executivo no Power BI:

`PNCP (data/raw) -> Python (src/limpeza.py e src/montar_tabelas.py) -> MySQL (Star Schema) -> Power BI (15+ Medidas DAX)`

```
.
├── data/
│   ├── raw/                  # CSVs brutos (compras.csv, itens.csv, resultados.csv)
│   └── processed/            # Tabelas sanitizadas e dimensionais (CSV)
├── docs/img/                  # Diagramas ER e figuras do planejamento
├── powerbi/                  # Relatório executivo (.pbix)
├── reports/                  # Notebooks de inspeção exploratória (Sprint 1)
├── sql/
│   ├── 01_criar_banco.sql    # DDL do esquema Star Schema no MySQL
│   └── 02_perguntas.sql      # Consultas SQL das perguntas de negócio (Sprint 5)
├── src/
│   ├── banco.py              # Conexão e executores no MySQL
│   ├── carregar.py           # Ingestão automatizada no banco (Sprint 4)
│   ├── config.py             # Configurações de ambiente e diretórios
│   ├── limpeza.py            # Funções puras de sanitização de dados (Sprint 2)
│   └── montar_tabelas.py     # Regras de negócio e Fato/Dimensões (Sprint 3)
├── .env.example              # Modelo de variáveis de ambiente
├── .gitignore                # Regras de exclusão do Git
├── requirements.txt          # Dependências Python
└── README.md                 # Documentação oficial do projeto

```

---
## 3. Dicionário dos Dados Brutos

A camada de dados brutos (`data/raw/`) é composta por três arquivos relacionáveis por `numero_controle_pncp` e `numero_item`:

* `compras.csv` (2.042 linhas): Cabeçalho dos certames licitatórios (órgãos, datas, modalidades e localidades).

* `itens.csv` (7.077 linhas): Detalhamento dos itens licitados (descrição, quantidade e valores estimados).

* `resultados.csv` (15.896 linhas): Registros de fornecedores classificados por item (CNPJ/CPF, valores homologados e cancelamentos).

---
## 4. Desenvolvimento do Projeto e Rastreabilidade por Sprints

O ciclo de desenvolvimento da esteira analítica foi gerenciado sob a metodologia ágil Kanban via GitHub Projects, dividido em 8 etapas/sprints de entrega incremental.


### 4.1. Sprint 0: Planejamento, Arquitetura e Configuração

* Estruturação do repositório no GitHub, definição da arquitetura de diretórios e padrões de código (`.gitignore`, `requirements.txt`).

* Configuração das variáveis de ambiente (`.env.example`) e centralização das configurações em `src/config.py`.

* Mapeamento inicial das 6 perguntas de negócio da Controladoria Geral.


### 4.2. Sprint 1 & 2: Auditoria e Sanitização de Dados (EDA & Engenharia)

A fase exploratória (`reports/inspecao.ipynb`) diagnosticou as anomalias da base bruta, tratadas pelas funções puras em `src/limpeza.py`:

* **Documentos (`limpar_documento`)**: Remoção de caracteres não numéricos e recomposição de zeros à esquerda (`.zfill()`) para CNPJ (14 dígitos) e CPF (11 dígitos).

* **Valores Monetários (`converter_numero`)**: Parser para cifrões (`R$`), inversão de separadores decimais/milhares e tratamento de negativos.

* **Inconsistências Temporais (`converter_data`)**: Parsing iterativo de datas e anulação de homologações anteriores à publicação.

* **Nulos Disfarçados (`limpar_texto`)**: Mapeamento de textos "zumbis" (`"N/A"`, `"NULL"`, `"-"`) e conversão para `None`/`NULL`.

* **Encoding e Texto (`padronizar_nome`)**: Correção de encoding (`Latin-1` -> `UTF-8`) e normalização em maiúsculas.

* **Autoteste Integrado**: 100% de aprovação nos 54 casos de teste de borda executados via `python -m src.limpeza`.
  

### 4.3. Sprint 3: Regras de Negócio e Montagem do Star Schema (ETL)

O script `src/montar_tabelas.py` consolida os dados limpos em `data/processed/` aplicando as diretrizes estratégicas:

1. **Grão da Fato**: 1 linha por item de contratação (`numero_controle_pncp` + `numero_item`).

2. **Vencedor por Item**: Descarte de cancelados e seleção do 1º colocado no SRP (desempate pelo menor `sequencial_resultado`).

3. **Filtro de Itens Validados**: Manutenção apenas de itens homologados e remoção de registros inconsistentes (quantidade <= 0, orçamento sigiloso, estimado < R\$ 1,00 ou divergência > 1.000x).

4. **Regra de Comparabilidade**: Trava para certames com disputa (exclui *Credenciamento* e razões fora do intervalo \[0,1; 10,0\]).

5. **Estruturação Dimensional**: Geração das tabelas `dim_orgao`, `dim_fornecedor`, `dim_modalidade`, `dim_localidade` e `fato_item_contratado` com chaves substitutas (`sk_`).
   
Ao final, a arquitetura em Star Schema fica assim:

<img width="1083" height="677" alt="Star Schema" src="https://github.com/user-attachments/assets/b86841a3-ea40-44f3-8a57-7af1ed3b9959" />


### 4.4. Sprint 4: Carga Automatizada e DW Relacional no MySQL

Persistência relacional gerenciada por `src/carregar.py`:

* **DDL Automatizado**: Execução do script `sql/01_criar_banco.sql` com criação da base `pncp_controladoria` e restrições de `PK`/`FK`.

* **Inserção Otimizada**: Ingestão em lote via `executemany` com tratamento automático de conversão de `NaN` para `NULL`.

* **Garantia de Integridade**: Carga estruturada alimentando primeiro as dimensões e finalizando na tabela fato.


### 4.5. Sprint 5: Consultas Analíticas e Perguntas de Negócio (SQL)

Consultas consolidadas em `sql/02_perguntas.sql` utilizando agregações ponderadas (`SUM ÷ SUM`) e tratamento com `NULLIF`:

* **P1 (Economia Global)**: Economia de **R\$ 992.861.686,95** (**14,46%** de desconto global sobre itens comparáveis).

* **P2 (Concentração & Risco)**: Top 10 fornecedores mapeados. O maior fornecedor isolado absorveu **R\$ 1,06 Bilhão** (13,18% de todo o orçamento contratado).

* **P3 (Modalidades)**: O *Pregão Eletrônico* despontou como a modalidade de maior eficiência e volume financeiro disputado.

* **P4 (Tempo de Ciclo)**: Tempo médio nacional de **48,1 dias** (máximo de 611 dias), identificando órgãos com gargalos operacionais superiores a 200 dias.

* **P5 (Distribuição Regional)**: Sudeste concentrou a maior fatia orçamentária, com variações significativas de desconto médio por UF.

* **P6 (Perfil dos Gastos)**: Consolidação do volume homologado em **Obras/Engenharia (60,8%)**, **Serviços (36,6%)** e **Bens (2,6%)**.

---
### 4.6. Sprint 6: Relatório Executivo e Dashboard no Power BI

Construção do painel interativo (`powerbi/pncp_analise_2.pbix`) integrado ao MySQL:

* **Páginas Temáticas**: 6 visualizações focadas em Visão Geral, Fornecedores, Modalidades, Ciclo de Compras, Mapa Geográfico (Shape Map) e Perfil dos Gastos.

* **Medidas DAX Destacadas**:

  ```
  Volume_Homologado = SUM(fato_item_contratado[valor_total_homologado])
  
  Economia_Nominal = CALCULATE(SUM(fato_item_contratado[economia_valor]), fato_item_contratado[comparavel] == 1)
  
  Pct_Economia = DIVIDE([Economia_Nominal], CALCULATE(SUM(fato_item_contratado[valor_total_estimado]), fato_item_contratado[comparavel] == 1), 0)
  
  Ciclo_Medio_Dias = AVERAGE(fato_item_contratado[dias_ciclo])
  
  ```

---
## 5. Desafios Técnicos Superados Durante a Execução

* **Diretórios Inexistentes (`OSError`)**: Resolvido com criação dinâmica via `Path.mkdir(parents=True, exist_ok=True)`.

* **Módulos Python (`ModuleNotFoundError`)**: Padronizada execução via flag modular (`python -m src.<modulo>`).

* **Tratamento de Divisão por Zero**: Uso sistemático de `NULLIF` no SQL e `DIVIDE()` no DAX.

* **Mapeamento da Categoria "Bens"**: Padronização dos termos originais (`Material`/`Compras`) via `CASE WHEN` no SQL e coluna calculada `Perfil_Gasto_Visual` no DAX.

* **Renderização Geográfica (UFs)**: Ajuste do Shape Map para consumir estritamente a sigla de 2 letras (`uf_sigla`), corrigindo falhas de acentuação nos nomes dos estados.

---
## 6. Prova Real e Validação de Resultados

Comparação e validação de 100% dos indicadores obtidos pela esteira analítica contra o gabarito de controle:

| Indicador | Valor Esperado | Valor Obtido no Pipeline | Status | 
| ----- | ----- | ----- | ----- | 
| Itens na Fato (`fato_item_contratado`) | 6.126 | 6.126 | ✅ Exato | 
| Fornecedores Distintos (`dim_fornecedor`) | 2.652 | 2.652 | ✅ Exato | 
| Unidades Compradoras (`dim_orgao`) | 363 | 363 | ✅ Exato | 
| Soma do Valor Total Homologado | R\$ 8.044.498.805,74 | R\$ 8.044.498.805,74 | ✅ Exato | 
| Soma do Valor Total Estimado (Todos) | R\$ 32.629.639.732,13 | R\$ 32.629.639.732,13 | ✅ Exato | 
| Itens Comparáveis | 5.457 | 5.457 | ✅ Exato | 
| Economia Nominal Comparável | R\$ 992.861.686,95 | R\$ 992.861.686,95 | ✅ Exato | 
| Economia % Comparável | 14,46% | 14,46% | ✅ Exato | 
| Itens com Ciclo Válido / Sem Ciclo | 5.896 / 230 | 5.896 / 230 | ✅ Exato | 
| Ciclo Médio / Máximo (Dias) | 48,1 / 611 dias | 48,1 / 611 dias | ✅ Exato | 
| Perfil do Gasto (% Volume) | Obras 60,8% · Servicos 36,6% · Bens 2,6% | Obras 60,8% · Servicos 36,6% · Bens 2,6% | ✅ Exato | 

---
## 7. Instruções de Reprodução e Execução

1. **Configurar o Ambiente Virtual Python**:

   ```
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   
   ```

2. **Configurar Variáveis de Ambiente**:
   Copie `.env.example` para `.env` e ajuste suas credenciais locais do MySQL:

   ```
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=sua_senha
   MYSQL_DATABASE=pncp_controladoria
   
   ```

3. **Executar Pipeline de ETL e Carga no Banco**:

   ```
   python -m src.montar_tabelas   # Sprint 3: Limpeza e geração dos CSVs processados
   python -m src.carregar         # Sprint 4: Criação do banco e carga no MySQL
   
   ```


---
Criado por Lilian Severino da Silva
