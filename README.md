# Esteira Analítica de Compras Públicas PNCP — Controladoria Geral

## 📌 Contextualização do Projeto (Sprint 0)
Este projeto foi desenvolvido como **Projeto Avaliativo do Módulo 2** do curso de Análise de Dados com Python, MySQL e Power BI. O objetivo principal é construir uma esteira analítica ponta a ponta (*End-to-End*) para auditar, sanitizar, modelar e visualizar dados brutos de contratações públicas federais extraídos do **Portal Nacional de Contratações Públicas (PNCP)** do ano de 2025.

A solução visa apoiar os órgãos de controle e transparência pública na identificação de gargalos operacionais severos, indícios de sobrepreço em itens homologados, concentração atípica de contratos em determinados fornecedores, morosidade entre a publicação de edital e a homologação e baixa adesão competitiva.

---

## 🛠️ Arquitetura da Solução & Estrutura de Diretórios (Sprint 0)
A aplicação segue uma arquitetura modular em camadas, integrando scripts de ETL, banco de dados relacional e dashboard executivo:

```text
.
├── data/
│   ├── raw/                  # CSVs brutos (compras.csv, itens.csv, resultados.csv)
│   └── processed/            # Tabelas sanitizadas e dimensionais (CSV)
├── docs/
│   └── img/                  # Diagramas e figuras do planejamento
│       └── sprints.png       # Registro visual do quadro de Sprints
├── powerbi/                  # Arquivo .pbix do Power BI
├── reports/                  # Relatórios e notebooks de inspeção
│   └── inspecao.ipynb        # Análise exploratória inicial (Sprint 1)
├── sql/
│   ├── 01_criar_banco.sql    # DDL do esquema Star Schema (MySQL)
│   └── 02_perguntas.sql      # Consultas SQL das 6 perguntas de negócio
├── src/
│   ├── banco.py              # Conexão e executores no MySQL
│   ├── carregar.py           # Ingestão automatizada no banco
│   ├── config.py             # Configurações e caminhos
│   ├── limpeza.py            # Funções puras de sanitização de dados
│   └── montar_tabelas.py     # Aplicação das regras de negócio e Fato/Dimensões
├── .env.example              # Modelo de credenciais do banco
├── .gitignore                # Arquivos ignorados pelo Git
├── requirements.txt          # Dependências Python
└── README.md                 # Documentação oficial do projeto


## 📖 Dicionário da Base Bruta (`data/raw/`) (Sprint 0)
- **`compras.csv`** (2.042 linhas): Cabeçalho dos edital/certames licitatórios (órgãos compradores, unidades, datas de publicação, modalidade e localidade)[cite: 3].
- **`itens.csv`** (7.077 linhas): Detalhe dos itens licitados em cada edital (descrição, quantidade, valores estimados e indicativos de sigilo/resultado)[cite: 3].
- **`resultados.csv`** (15.896 linhas): Fornecedores classificados por item (CNPJ/CPF, valores homologados, ordenação SRP e cancelamentos)[cite: 3].

---

## 🔍 Auditoria de Dados e Mapeamento de Anomalias (Sprint 1)
Antes de qualquer processo de higienização, os arquivos brutos armazenados na pasta `data/raw/` foram inspecionados no notebook `reports/inspecao.ipynb` com leitura estrita em formato de texto (`dtype=str` e `keep_default_na=False`) para evitar o mascaramento de erros de tipagem[cite: 3, 4, 10].

As principais falhas de qualidade identificadas foram[cite: 3]:

| Categoria | Arquivo / Campo Atingido | Anomalia Identificada nos Dados Brutos | Racional de Higienização Previsto |
| :--- | :--- | :--- | :--- |
| **Documentos** | `compras.csv` (`cnpj_orgao`) e `resultados.csv` (`ni_fornecedor`) | Presença de pontuações de máscara (`.`, `/`, `-`), perda de zeros à esquerda por conversões prévias (12/13 dígitos) e mistura de tipos de pessoa (PJ/PF/PE)[cite: 3, 9, 10]. | Limpeza de caracteres não numéricos e recomposição de zeros à esquerda via `.zfill()` em `limpeza.limpar_documento`[cite: 3, 9]. |
| **Valores Monetários** | `itens.csv` e `resultados.csv` (`valor_unitario_*`, `valor_total_*`, `quantidade`) | Preços e quantidades gravados como texto contendo `R$`, separadores de decimal/milhar não padronizados (`0,754`, `746.815`) e números negativos entre parênteses `(1.500,00)`[cite: 3, 9]. | Parser numérico customizado em `limpeza.converter_numero` tratando vírgulas, pontos e sinais[cite: 3, 9]. |
| **Inconsistência Temporal** | `compras.csv` (`data_publicacao`) e `resultados.csv` (`data_resultado`) | Presença de múltiplas máscaras temporais (ISO com hora, `DD/MM/YYYY`) e registros em que a homologação é anterior à publicação do edital[cite: 3, 9, 10]. | Normalização de formatos via `limpeza.converter_data` e anulação da data de homologação/ciclo em violações cronológicas[cite: 3, 9, 10]. |
| **Nulos Disfarçados** | Diversas colunas de texto em todos os arquivos | Preenchimento de ausência de valor com strings "zumbis": `"N/A"`, `"NULL"`, `"-"`, `"SEM INFORMAÇÃO"`, `"NÃO INFORMADO"`, `"0"`[cite: 3, 9]. | Mapeamento no conjunto `NULOS` e conversão unificada para `None`/`NULL` em `limpeza.limpar_texto`[cite: 3, 9]. |
| **Encoding e Texto** | `objeto_compra`, `descricao`, nomes de órgãos e fornecedores | Caracteres acentuados corrompidos por divergência de encoding (`Latin-1` lido como `UTF-8`, ex.: `AquisiÃ§Ã£o`), espaços múltiplos e hífens desalinhados[cite: 3, 9]. | Re-encoding `latin-1` ➔ `utf-8`, remoção de caracteres invisíveis e padronização em maiúsculas via `limpeza.padronizar_nome`[cite: 3, 9]. |
