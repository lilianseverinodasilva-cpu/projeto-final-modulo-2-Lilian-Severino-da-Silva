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
