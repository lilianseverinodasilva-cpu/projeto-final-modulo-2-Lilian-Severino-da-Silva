# Esteira Analitica de Compras Publicas PNCP - Controladoria Geral

## Indice
1. [Contextualizacao do Projeto](#1-contextualizacao-do-projeto)
2. [Arquitetura da Solucao e Estrutura de Pastas](#2-arquitetura-da-solucao-e-estrutura-de-pastas)
3. [Dicionario dos Dados Brutos](#3-dicionario-dos-dados-brutos)
4. [Auditoria de Dados e Mapeamento de Anomalias (Sprint 1)](#4-auditoria-de-dados-e-mapeamento-de-anomalias-sprint-1)
5. [Sanitizacao e Limpeza de Dados em Python (Sprint 2)](#5-sanitizacao-e-limpeza-de-dados-em-python-sprint-2)
6. [Regras de Negocio e Montagem das Tabelas (Sprint 3)](#6-regras-de-negocio-e-montagem-das-tabelas-sprint-3)
7. [Carga Automatizada e Modelagem Star Schema no MySQL (Sprint 4)](#7-carga-automatizada-e-modelagem-star-schema-no-mysql-sprint-4)
8. [Desafios Técnicos e Soluções Adotadas](#8-desafios-tecnicos-e-solucoes-adotadas)
9. [Conferencia de Resultados e Prova Real](#9-conferencia-de-resultados-e-prova-real)
10. [Planejamento de Sprints e Rastreabilidade](#10-planejamento-de-sprints-e-rastreabilidade)
11. [Instrucoes de Reproducao e Execucao](#11-instrucoes-de-reproducao-e-execucao)

---

## 1. Contextualizacao do Projeto
Este projeto foi desenvolvido como Projeto Avaliativo do Modulo 2 do curso de Analise de Dados com Python, MySQL e Power BI. O objetivo e construir uma esteira analitica ponta a ponta (End-to-End) para auditar, sanitizar, modelar e visualizar dados brutos de contratacoes publicas federais extraidos do Portal Nacional de Contratacoes Publicas (PNCP) referentes ao ano de 2025.

A aplicacao visa fornecer subsidios tecnicos para orgaos de controle e transparencia publica na identificacao de gargalos operacionais, indicios de sobrepreco em itens homologados, concentracao atipica de contratos em determinados fornecedores, morosidade excessiva entre a publicacao de edital e a homologacao e baixa adesao competitiva em certas modalidades licitatorias.

---

## 2. Arquitetura da Solucao e Estrutura de Pastas
A esteira analitica foi desenvolvida em uma arquitetura modular em camadas, integrando scripts de ETL em Python, modelagem dimensional em banco de dados relacional MySQL e relatorio executivo no Power BI:

`PNCP (data/raw) -> Python (src/limpeza.py e src/montar_tabelas.py) -> MySQL (Star Schema) -> Power BI (15+ Medidas DAX)`

```text
.
├── data/
│   ├── raw/                  # CSVs brutos (compras.csv, itens.csv, resultados.csv)
│   └── processed/            # Tabelas sanitizadas e dimensionais (CSV)
├── docs/
│   └── img/                  # Diagramas ER e figuras do planejamento
│       └── sprints.png       # Registro visual do quadro de Sprints
├── powerbi/                  # Relatorio executivo (.pbix)
├── reports/                  # Notebooks de inspecao e relatorios
│   └── inspecao.ipynb        # Analise exploratoria inicial (Sprint 1)
├── sql/
│   ├── 01_criar_banco.sql    # DDL do esquema Star Schema (MySQL)
│   └── 02_perguntas.sql      # Consultas SQL das 6 perguntas de negocio
├── src/
│   ├── banco.py              # Conexao e executores no MySQL
│   ├── carregar.py           # Ingestao automatizada no banco
│   ├── config.py             # Configuracoes de ambiente e diretarios
│   ├── limpeza.py            # Funcoes puras de sanitizacao de dados
│   └── montar_tabelas.py     # Aplicacao das regras de negocio e Fato/Dimensoes
├── .env.example              # Modelo de variaveis de ambiente

````
---

## 3. Dicionario dos Dados Brutos
A camada de dados brutos (`data/raw/`) e composta por tres arquivos relacionaveis pelo identificador `numero_controle_pncp` (e `numero_item`)[cite: 3]:

- `compras.csv` (2.042 linhas): Cabecalho dos certames licitatorios, contendo dados dos orgaos compradores, unidades, datas de publicacao, modalidade e localidade[cite: 3].
- `itens.csv` (7.077 linhas): Detalhamento dos itens licitados em cada edital, incluindo descricao, quantidade, valores estimados e indicativos de sigilo e resultado[cite: 3].
- `resultados.csv` (15.896 linhas): Registros dos fornecedores classificados por item, com CNPJ/CPF, valores homologados, ordenacao SRP e cancelamentos[cite: 3].

---

## 4. Auditoria de Dados e Mapeamento de Anomalias (Sprint 1)
Na fase inicial de inspecao exploratoria (`reports/inspecao.ipynb`), a leitura dos arquivos brutos foi executada com tipagem estrita em texto (`dtype=str` e `keep_default_na=False`) para evitar a conversao automatica e o mascaramento de falhas de qualidade[cite: 3, 4].

As anomalias catalogadas na base bruta incluem[cite: 3]:

| Categoria | Arquivo / Campo | Anomalia Identificada | Racional da Higienizacao |
| :--- | :--- | :--- | :--- |
| Documentos | `compras.csv` (`cnpj_orgao`) e `resultados.csv` (`ni_fornecedor`) | Pontuacoes de mascara (`.`, `/`, `-`), perda de zeros a esquerda (12 ou 13 digitos) e mistura de tipos de pessoa (PJ/PF/PE)[cite: 3]. | Remocao de caracteres nao numericos e recomposicao de zeros a esquerda via `.zfill()` em `limpeza.limpar_documento`[cite: 3]. |
| Valores Monetarios | `itens.csv` e `resultados.csv` (`valor_unitario_*`, `valor_total_*`, `quantidade`) | Precos e quantidades gravados em texto com cifrao (`R$`), separadores de decimal e milhar nao padronizados (`0,754` e `746.815`) e valores negativos entre parenteses[cite: 3]. | Parser numerico customizado em `limpeza.converter_numero` tratando virgulas, pontos isolados/repetidos e sinais[cite: 3]. |
| Inconsistencia Temporal | `compras.csv` (`data_publicacao`) e `resultados.csv` (`data_resultado`) | Presenca de multiplas mascaras temporais (ISO com hora, `DD/MM/YYYY`) e homologacoes anteriores a publicacao do edital[cite: 3]. | Normalizacao de formatos em `limpeza.converter_data` e anulacao da data de homologacao/ciclo em violacoes cronologicas[cite: 3]. |
| Nulos Disfarçados | Diversas colunas de texto | Presenca de strings "zumbis" representando ausencias de valor: `"N/A"`, `"NULL"`, `"-"`, `"SEM INFORMACAO"`, `"NAO INFORMADO"`, `"0"`[cite: 3]. | Mapeamento no conjunto `NULOS` e conversao unificada para `None`/`NULL` em `limpeza.limpar_texto`[cite: 3]. |
| Encoding e Texto | `objeto_compra`, `descricao`, nomes | Acentuacao corrompida por divergencia de encoding (`Latin-1` lido como `UTF-8`) e espacamentos multiplos[cite: 3]. | Re-encoding `latin-1` -> `utf-8`, remocao de caracteres invisiveis de largura zero e padronizacao em maiusculas via `limpeza.padronizar_nome`[cite: 3]. |

---

## 5. Sanitizacao e Limpeza de Dados em Python (Sprint 2)
No modulo `src/limpeza.py`, foram implementadas as funcoes puras de tratamento dos dados brutos[cite: 3]:

- `limpar_texto(texto, zero_eh_nulo)`: Remove caracteres invisiveis, corrige encodings corrompidos, elimina espacos excedentes e converte nulos ocultos para `None`[cite: 3].
- `padronizar_nome(texto)`: Converte textos para caixa alta e padroniza o espacamento em hifens[cite: 3].
- `limpar_documento(texto, tipo_pessoa)`: Isola caracteres numericos e aplica `.zfill(14)` para PJ e `.zfill(11)` para PF[cite: 3].
- `converter_numero(texto)`: Trata marcadores monetarios, identifica numeros negativos e converte strings numericas com suporte a padroes mistos de separadores decimais e de milhar[cite: 3].
- `converter_data(texto)`: Trunca a porcao de hora e realiza o parsing iterativo sobre multiplos formatos de data validando o intervalo util entre 2000 e 2030[cite: 3].

O autoteste integrado (`python -m src.limpeza`) validou a execucao das funcoes, obtendo 100% de aprovacao nos 54 casos de teste de borda.

---

## 6. Regras de Negocio e Montagem das Tabelas (Sprint 3)
O script `src/montar_tabelas.py` aplica as regras de negocio definidas pela Controladoria sobre os dados brutos, gerando a camada de dados processados em `data/processed/`[cite: 3]:

1. **Grao da Fato**: Definido estritamente em uma linha por item de contratacao (`numero_controle_pncp` + `numero_item`)[cite: 3].
2. **Vencedor por Item**: Descarte primario de resultados cancelados (`data_cancelamento` preenchida) e selecao do 1º colocado no Sistema de Registro de Precos (`ordem_classificacao_srp`)[cite: 3]. Em caso de empate, utiliza-se o menor `sequencial_resultado`[cite: 3].
3. **Filtro de Itens com Resultado**: Junção restrita aos itens com fornecedor vencedor homologado (`how="inner"`)[cite: 3].
4. **Criterio de Rejeicao de Itens**: Descarte de itens com dados inconsistentes (quantidade ou valor unitario estimado/homologado <= 0, orcamento sigiloso, valor total estimado < R$ 1,00, valor total homologado > 1.000x o estimado ou valores superiores a R$ 1 trilhao)[cite: 3].
5. **Comparabilidade e Economia**: A economia nominal (`valor_total_estimado - valor_total_homologado`) e restrita aos itens comparaveis (modalidade diferente de Credenciamento e razao homologado/estimado entre 0,1 e 10)[cite: 3].
6. **Cronologia**: Anulacao da data de homologacao e do ciclo para certames com data de resultado anterior a data de publicacao[cite: 3].
7. **Perfil do Gasto**: Classificacao dos itens em Bens, Serviços ou Obras e engenharia atraves de expressoes regulares com limite de palavra (`\b`) aplicadas sobre a descricao do item e objeto da compra[cite: 3].
8. **Modelagem de Dimensoes**: Criacao das 4 tabelas de dimensao (`dim_orgao`, `dim_fornecedor`, `dim_modalidade`, `dim_localidade`) com chaves substitutas (`sk_`) sequenciais e substituicao das chaves naturais na Fato[cite: 3].

---

## 7. Carga Automatizada e Modelagem Star Schema no MySQL (Sprint 4)
O modulo `src/carregar.py` automatiza a persistência relacional do Data Warehouse no MySQL[cite: 3]:

1. **Schema DDL**: Execucao automatizada do script `sql/01_criar_banco.sql` para criacao do banco `pncp_controladoria` e definicao estrutural de tabelas com chaves primárias e estrangeiras (`CONSTRAINT fk_*`)[cite: 3].
2. **Carga em Lote (Batch Processing)**: Inserção otimizada utilizando o método `executemany` do driver `mysql-connector-python`, agilizando a gravação de milhares de registros[cite: 3].
3. **Respeito à Dependência Relacional**: As 4 tabelas dimensionais são inseridas primeiro para garantir a integridade referencial antes da carga da tabela `fato_item_contratado`[cite: 3].
4. **Tratamento de Nulos**: Mapeamento seguro de valores vazios e `NaN` do Pandas para `NULL` no banco de dados relacional.

---

## 8. Desafios Técnicos e Soluções Adotadas
Durante a execução das Sprints 3 e 4, diversos desafios de ambiente e estruturação foram superados:

* **Ausência de Diretório Processado (`OSError`)**: Como o Git não versiona pastas vazias, o Pandas gerava erro ao tentar exportar os arquivos para `data/processed/`. A solução foi implementar a criação dinâmica de diretórios com `Path.mkdir(parents=True, exist_ok=True)` no script de montagem.
* **Erros de Sintaxe no Módulo Python (`ModuleNotFoundError: No module named 'src'`)**: Causados pela execução direta de scripts usando caminhos absolutos ou posicionado na pasta raiz incorreta do sistema operacional. O problema foi sanado consolidando o uso do padrão de execução modular do Python (`python -m src.<nome_modulo>`) a partir da raiz do repositório.
* **Credenciais e Acesso ao Banco (`Access Denied`)**: Incompatibilidades iniciais com a autenticação do MySQL `root` foram resolvidas por meio da configuração correta do arquivo de ambiente `.env` e validação do serviço local na porta `3306`.
* **Tratamento de Intervalos Temporais (`Datetime to Days`)**: Na modelagem do ciclo de compras, a subtração de datas gerava objetos `timedelta` do Python; a conversão correta para contagem inteira de dias foi efetuada mapeando o atributo `.days` com validação de nulos.

---

## 9. Conferencia de Resultados e Prova Real
A execucao de `src/montar_tabelas.py` e da carga em `src/carregar.py` consolida a base limpa e validada contra o gabarito oficial da Prova Real[cite: 3]:

| Indicador | Valor Esperado | Valor Obtido no Pipeline |
| :--- | :---: | :---: |
| Linhas de compras.csv | 2.042 | 2.042 |
| Linhas de itens.csv | 7.077 | 7.077 |
| Linhas de resultados.csv | 15.896 | 15.896 |
| Itens sem resultado homologado | 852 | 852 |
| Itens Rejeitados | 99 | 99 |
| Itens na Fato (fato_item_contratado) | 6.126 | 6.126 |
| Contratacoes distintas na Fato | 1.962 | 1.962 |
| Fornecedores distintos (dim_fornecedor) | 2.652 | 2.652 |
| Unidades compradoras (dim_orgao) | 363 | 363 |
| Soma do Valor Total Homologado | R$ 8.044.498.805,74 | R$ 8.044.498.805,74 |
| Soma do Valor Total Estimado (Todos) | R$ 32.629.639.732,13 | R$ 32.629.639.732,13 |
| Itens Comparaveis | 5.457 | 5.457 |
| Soma do Estimado Comparavel | R$ 6.867.663.469,91 | R$ 6.867.663.469,91 |
| Economia Nominal Comparavel | R$ 992.861.686,95 | R$ 992.861.686,95 |
| Economia % Comparavel | 14,46% | 14,46% |
| Itens com Ciclo Valido | 5.896 | 5.896 |
| Itens sem Ciclo | 230 | 230 |
| Ciclo Medio / Maximo | 48,1 / 611 dias | 48,1 / 611 dias |
| Perfil do Gasto (% Volume) | Obras 60,8% · Servicos 36,6% · Bens 2,6% | Obras 60,8% · Servicos 36,6% · Bens 2,6% |

---

## 10. Planejamento de Sprints e Rastreabilidade
O desenvolvimento do projeto foi conduzido utilizando a metodologia Kanban no GitHub Projects, organizado em 8 Sprints de entrega[cite: 3]:

![Sprints do Projeto](docs/img/sprints.png)

- **Sprint 0**: Estruturacao do repositorio, planejamento e diagnostico inicial dos arquivos brutos[cite: 3].
- **Sprint 1**: Auditoria quantitativa das inconsistencias em `reports/inspecao.ipynb`[cite: 3].
- **Sprint 2**: Desenvolvimento e validacao das funcoes puras de tratamento em `src/limpeza.py`[cite: 3].
- **Sprint 3**: Aplicacao das regras de negocio e exportacao das tabelas em `src/montar_tabelas.py`[cite: 3].
- **Sprint 4**: Modelagem Star Schema no MySQL e ingestao automatizada em lote (`src/carregar.py`)[cite: 3].
- **Sprint 5**: Elaboracao das consultas SQL analiticas (`sql/02_perguntas.sql`)[cite: 3].
- **Sprint 6**: Construcao do dashboard executivo no Power BI com 15+ medidas DAX e usabilidade CRAP[cite: 3].
- **Sprint 7**: Documentacao final do repositorio, geracao dos artefatos visuais e gravacao do video de Review[cite: 3].

---

## 11. Instrucoes de Reproducao e Execucao

1. **Configurar o Ambiente Virtual Python**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ````
2. Configurar as Variáveis de Ambiente:
Copie o arquivo .env.example para .env e preencha com suas credenciais locais do MySQL:
├── .gitignore                # Regras de exclusao do Git
├── requirements.txt          # Dependencias do projeto Python
└── README.md                 # Documentacao oficial do projeto

````
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=sua_senha
MYSQL_DATABASE=pncp_controladoria
````

3. Executar a Esteira ETL (Sprint 3):

````python -m src.montar_tabelas````

4. Executar a Carga no Banco de Dados (Sprint 4):

```` python -m src.carregar ````

