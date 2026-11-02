# Esteira Analítica de Compras Públicas PNCP - Controladoria Geral

## Índice
1. [Contextualização do Projeto](#1-contextualizacao-do-projeto)
2. [Arquitetura da Solução e Estrutura de Pastas](#2-arquitetura-da-solucao-e-estrutura-de-pastas)
3. [Dicionário dos Dados Brutos](#3-dicionario-dos-dados-brutos)
4. [Auditoria e Sanitização de Dados (Sprints 1 e 2)](#4-auditoria-e-sanitizacao-de-dados-sprints-1-e-2)
5. [Regras de Negócio e Montagem da Fato/Dimensões (Sprint 3)](#5-regras-de-negocio-e-montagem-da-fatodimensoes-sprint-3)
6. [Carga Automatizada e Star Schema no MySQL (Sprint 4)](#6-carga-automatizada-e-star-schema-no-mysql-sprint-4)
7. [Consultas Analíticas e Perguntas de Negócio em SQL (Sprint 5)](#7-consultas-analiticas-e-perguntas-de-negocio-em-sql-sprint-5)
8. [Relatório Executivo e Dashboard no Power BI (Sprint 6)](#8-relatorio-executivo-e-dashboard-no-power-bi-sprint-6)
9. [Desafios Técnicos e Soluções Adotadas](#9-desafios-tecnicos-e-solucoes-adotadas)
10. [Conferência de Resultados e Prova Real](#10-conferencia-de-resultados-e-prova-real)
11. [Planejamento de Sprints e Rastreabilidade](#11-planejamento-de-sprints-e-rastreabilidade)
12. [Instruções de Reprodução e Execução](#12-instrucoes-de-reproducao-e-execucao)

---

## 1. Contextualização do Projeto
Este projeto constrói uma esteira analítica ponta a ponta (End-to-End) para auditar, sanitizar, modelar e visualizar dados brutos de contratações públicas federais extraídos do Portal Nacional de Contratações Públicas (PNCP) referentes a 2025. O objetivo é fornecer subsídios técnicos para órgãos de controle na identificação de gargalos operacionais, indícios de sobrepreço, concentração atípica de contratos, morosidade licitatória e baixa competitividade.

---

## 2. Arquitetura da Solução e Estrutura de Pastas
A esteira integra scripts de ETL em Python, Data Warehouse (Star Schema) no MySQL e relatório executivo no Power BI:

`PNCP (data/raw) -> Python (src/limpeza.py e src/montar_tabelas.py) -> MySQL (Star Schema) -> Power BI (15+ Medidas DAX)`

```text
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
- `compras.csv` (2.042 linhas): Cabeçalho dos certames licitatórios (órgãos, datas, modalidades e localidades).
- `itens.csv` (7.077 linhas): Detalhamento dos itens licitados (descrição, quantidade e valores estimados).
- `resultados.csv` (15.896 linhas): Registros de fornecedores classificados por item (CNPJ/CPF, valores homologados e cancelamentos).

---

## 4. Auditoria e Sanitização de Dados (Sprints 1 e 2)
A fase exploratória (`reports/inspecao.ipynb`) identificou anomalias na base bruta, tratadas pelas funções puras do módulo `src/limpeza.py`:
- **Documentos (`limpar_documento`)**: Remoção de caracteres não numéricos e recomposição de zeros à esquerda (`.zfill()`) para CNPJ (14 dígitos) e CPF (11 dígitos).
- **Valores Monetários (`converter_numero`)**: Parser numérico para tratar cifrões (`R$`), inversão de separadores decimais/milhares (`0,754` e `746.815`) e números negativos entre parênteses.
- **Inconsistências Temporais (`converter_data`)**: Parsing iterativo em múltiplos formatos de data e anulação de homologações anteriores à publicação do edital.
- **Nulos Disfarçados (`limpar_texto`)**: Mapeamento de textos "zumbis" (`"N/A"`, `"NULL"`, `"-"`, `"SEM INFORMACAO"`) e conversão padronizada para `None`/`NULL`.
- **Encoding e Texto (`padronizar_nome`)**: Correção de encoding (`Latin-1` -> `UTF-8`) e padronização em maiúsculas sem espaços extras.

*O autoteste integrado (`python -m src.limpeza`) obteve 100% de aprovação nos 54 casos de teste de borda.*

---

## 5. Regras de Negócio e Montagem da Fato/Dimensões (Sprint 3)
O script `src/montar_tabelas.py` consolida os dados limpos em `data/processed/` aplicando as regras do projeto:
1. **Grão da Fato**: 1 linha por item de contratação (`numero_controle_pncp` + `numero_item`).
2. **Vencedor por Item**: Descarte de resultados cancelados e seleção do 1º colocado no SRP (desempate pelo menor `sequencial_resultado`).
3. **Filtro de Itens Validados**: Manutenção apenas de itens com vencedor homologado e remoção de registros inconsistentes (quantidade <= 0, orçamento sigiloso, total estimado < R$ 1,00 ou divergência > 1.000x).
4. **Regra de Comparabilidade**: Restrita aos certames com disputa (exclui *Credenciamento* e razões homologado/estimado fora do intervalo [0,1; 10,0]).
5. **Modelagem Star Schema**: Geração de 4 tabelas dimensionais (`dim_orgao`, `dim_fornecedor`, `dim_modalidade`, `dim_localidade`) com chaves substitutas (`sk_`).

---

## 6. Carga Automatizada e Star Schema no MySQL (Sprint 4)
O módulo `src/carregar.py` automatiza a persistência relacional do Data Warehouse no MySQL:
- **DDL Automatizado**: Execução do `sql/01_criar_banco.sql` para criação da base `pncp_controladoria` e restrições de chaves (`PK`/`FK`).
- **Carga em Lote (`executemany`)**: Otimização de inserção massiva de registros com mapeamento automático de `NaN` para `NULL`.
- **Integridade Referencial**: Carga ordenada inserindo primeiro as dimensões e posteriormente a `fato_item_contratado`.

---

## 7. Consultas Analíticas e Perguntas de Negócio em SQL (Sprint 5)
As consultas estruturadas em `sql/02_perguntas.sql` respondem às questões centrais da Controladoria, respeitando rigorosamente as diretrizes técnicas de agregação (`SOMA ÷ SOMA`, `NULLIF` e filtros de comparabilidade):

- **Pergunta 1 (Economia Global)**: O governo economizou **R$ 992.861.686,95** sobre os itens comparáveis, representando uma taxa de economia global de **14,46%** (Soma Estimado: R$ 6,86 Bi | Soma Homologado: R$ 5,87 Bi).
- **Pergunta 2 (Concentração e Risco de Fornecedores)**: Mapeamento dos 10 maiores fornecedores com cálculo de representatividade via subconsulta. O maior fornecedor isolado concentrou **R$ 1,06 Bilhão** (13,18% de todo o orçamento público do PNCP 2025).
- **Pergunta 3 (Economia e Eficiência por Modalidade)**: O *Pregão Eletrônico* apresentou a maior eficiência e volume financeiro em disputa, enquanto modalidades diretas sem disputa ostensiva apresentaram os menores percentuais de desconto.
- **Pergunta 4 (Tempo do Ciclo de Compras)**: O ciclo médio nacional foi de **48,1 dias** (máximo de 611 dias). A consulta por órgão (`HAVING COUNT >= 5`) evidenciou instituições com morosidade superior a 200 dias entre edital e homologação.
- **Pergunta 5 (Distribuição Regional)**: A Região Sudeste concentrou o maior volume financeiro total, enquanto análises por UF revelaram variações significativas nos índices médios de desconto.
- **Pergunta 6 (Perfil dos Gastos)**: A distribuição do volume homologado consolidou-se em **Obras e Engenharia (60,8%)**, **Serviços (36,6%)** e **Bens (2,6%)**.

---

## 8. Relatório Executivo e Dashboard no Power BI (Sprint 6)
O relatório interativo (`powerbi/pncp_analise_2.pbix`) consome o modelo relacional em Star Schema do MySQL e implementa 15+ medidas DAX otimizadas para responder às 6 perguntas de negócio com design profissional e foco executivo.

### 8.1. Estrutura das Páginas do Relatório
- **Página 1 - Visão Geral & Economia Global**: KPIs de topo para Volume Homologado (R$ 8,04 Bi), Volume Estimado Comparável (R$ 6,86 Bi), Volume Homologado Comparável (R$ 5,87 Bi), Economia Nominal (R$ 992,86 Mi) e % de Economia (14,46%).
- **Página 2 - Concentração e Risco de Fornecedores**: Gráfico de barras horizontais com o Top 10 fornecedores por volume financeiro e indicação de participação percentual sobre o orçamento global.
- **Página 3 - Eficiência por Modalidade**: Análise comparativa entre modalidades licitatórias com matriz de desconto e volume financeiro sob disputa.
- **Página 4 - Tempo do Ciclo de Compras**: Histograma e cartões com o tempo médio de ciclo (48,1 dias) e identificação das unidades compradoras com maior tempo entre a publicação do edital e a homologação.
- **Página 5 - Distribuição Regional dos Gastos**: Visual geográfico (Shape Map) integrado com a dimensão de localidade (`dim_localidade[uf_sigla]`), apresentando a distribuição financeira por estado e grande região.
- **Página 6 - Perfil dos Gastos (Bens, Serviços e Obras)**: Gráfico de rosca e matriz executiva para visualização do volume homologado e percentual de economia nas três macrocategorias do setor público.

### 8.2. Principais Medidas DAX Implementadas
- **Volume Total Homologado**: 
  ```dax
  Volume_Homologado = SUM(fato_item_contratado[valor_total_homologado])
  ```
- **Economia Nominal Comparável**: 
  ```dax
  Economia_Nominal = CALCULATE(SUM(fato_item_contratado[economia_valor]), fato_item_contratado[comparavel] == 1)
  ```
- **Percentual de Economia**: 
  ```dax
  Pct_Economia = DIVIDE([Economia_Nominal], CALCULATE(SUM(fato_item_contratado[valor_total_estimado]), fato_item_contratado[comparavel] == 1), 0)
  ```
- **Ciclo Médio de Compras (Dias)**: 
  ```dax
  Ciclo_Medio_Dias = AVERAGE(fato_item_contratado[dias_ciclo])
  ```
- **Perfil de Gasto Visual (Tratamento de Rótulos)**:
  ```dax
  Perfil_Gasto_Visual = 
  VAR _Texto = LOWER(TRIM(fato_item_contratado[perfil_gasto]))
  RETURN
      SWITCH(
          TRUE(),
          CONTAINSSTRING(_Texto, "material") || CONTAINSSTRING(_Texto, "compra") || CONTAINSSTRING(_Texto, "bem"), "Bens",
          CONTAINSSTRING(_Texto, "servico") || CONTAINSSTRING(_Texto, "serviço"), "Serviços",
          CONTAINSSTRING(_Texto, "obra") || CONTAINSSTRING(_Texto, "engenharia"), "Obras",
          "Outros"
      )
  ```

---

## 9. Desafios Técnicos e Soluções Adotadas
- **Estrutura de Pastas Inexistente (`OSError`)**: Criada rotina para verificação e geração automática de diretórios via `Path.mkdir(parents=True, exist_ok=True)`.
- **Importação de Módulos (`ModuleNotFoundError`)**: Padronizada a execução modular a partir do diretório raiz utilizando a flag de módulo (`python -m src.<modulo>`).
- **Erros de Tipagem e Sintaxe SQL (`Error 1054`)**: Adequadas as consultas aos nomes exatos das colunas da DDL e substituído `COUNT(f.id)` por `COUNT(*)`.
- **Tratamento de Divisão por Zero**: Aplicado `NULLIF(denominador, 0)` nas queries SQL e a função `DIVIDE()` no DAX para garantir estabilidade em categorias sem itens comparáveis.
- **Mapeamento da Categoria "Bens" na API**: Rótulos nativos cadastrados como `Material` e `Compras` foram padronizados via `CASE WHEN` no SQL e coluna calculada `Perfil_Gasto_Visual` no Power BI.
- **Compatibilidade do Shape Map (UFs)**: Falhas de renderização em nomes com acentuação corrigidas com o uso estrito de siglas de 2 letras (`uf_sigla`).

---

## 10. Conferência de Resultados e Prova Real
A esteira de dados foi validada contra o gabarito oficial do projeto, obtendo 100% de paridade em todos os indicadores:

| Indicador | Valor Esperado | Valor Obtido no Pipeline | Status |
| :--- | :---: | :---: | :---: |
| Itens na Fato (`fato_item_contratado`) | 6.126 | 6.126 | ✅ Exato |
| Fornecedores Distintos (`dim_fornecedor`) | 2.652 | 2.652 | ✅ Exato |
| Unidades Compradoras (`dim_orgao`) | 363 | 363 | ✅ Exato |
| Soma do Valor Total Homologado | R$ 8.044.498.805,74 | R$ 8.044.498.805,74 | ✅ Exato |
| Soma do Valor Total Estimado (Todos) | R$ 32.629.639.732,13 | R$ 32.629.639.732,13 | ✅ Exato |
| Itens Comparáveis | 5.457 | 5.457 | ✅ Exato |
| Economia Nominal Comparável | R$ 992.861.686,95 | R$ 992.861.686,95 | ✅ Exato |
| Economia % Comparável | 14,46% | 14,46% | ✅ Exato |
| Itens com Ciclo Válido / Sem Ciclo | 5.896 / 230 | 5.896 / 230 | ✅ Exato |
| Ciclo Médio / Máximo (Dias) | 48,1 / 611 dias | 48,1 / 611 dias | ✅ Exato |
| Perfil do Gasto (% Volume) | Obras 60,8% · Servicos 36,6% · Bens 2,6% | Obras 60,8% · Servicos 36,6% · Bens 2,6% | ✅ Exato |

---

## 11. Planejamento de Sprints e Rastreabilidade
O projeto foi conduzido via metodologia Kanban no GitHub Projects, estruturado em 8 Sprints:
- **Sprint 0**: Planejamento e estrutura do repositório.
- **Sprint 1**: Auditoria de qualidade em `reports/inspecao.ipynb`.
- **Sprint 2**: Funções puras de sanitização em `src/limpeza.py`.
- **Sprint 3**: Regras de negócio e geração da Fato/Dimensões em `src/montar_tabelas.py`.
- **Sprint 4**: Modelagem Star Schema e carga em lote no MySQL (`src/carregar.py`).
- **Sprint 5**: Consultas analíticas e perguntas de negócio (`sql/02_perguntas.sql`).
- **Sprint 6**: Dashboard executivo no Power BI com 15+ medidas DAX.
- **Sprint 7**: Documentação final, artefatos visuais e gravação do vídeo de Review.

---

## 12. Instruções de Reprodução e Execução

1. **Configurar o Ambiente Virtual Python**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configurar Variáveis de Ambiente**:
   Copie `.env.example` para `.env` e ajuste suas credenciais locais do MySQL:
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=sua_senha
   MYSQL_DATABASE=pncp_controladoria
   ```

3. **Executar Pipeline de ETL e Carga no Banco**:
   ```bash
   python -m src.montar_tabelas   # Sprint 3: Limpeza e geração dos CSVs processados
   python -m src.carregar         # Sprint 4: Criação do banco e carga no MySQL
   ```

---

Criado por Lilian Severino da Silva