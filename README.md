# Análise Reproduutiva de Ovinos

Aplicação web (Streamlit) para análise de dados reprodutivos de ovinos submetidos a protocolos de **IATF (Inseminação Artificial em Tempo Fixo)**, desenvolvida no âmbito de um projeto PIBIC.

O usuário envia uma planilha Excel preenchida com os dados dos animais e recebe automaticamente indicadores, gráficos e um relatório final em PDF.

## Funcionalidades

- **Download do modelo de planilha** (`Modelo_Dados_Ovinos_IATF.xlsx`) para preenchimento padronizado dos dados.
- **Upload e validação** da planilha preenchida, com checagem das colunas obrigatórias.
- **Indicadores (KPIs)**: total de animais, número de carneiros, taxa de prenhez final e número de fêmeas vazias.
- **Análise por estação de monta** (até 3 estações): animais submetidos, diagnósticos válidos, prenhes, vazias e taxa de prenhez, com gráficos de barras e pizza.
- **Diagnósticos de gestação por etapa** (inicial, estações 1–3 e final), detalhados em tabelas e gráficos.
- **Desempenho por carneiro**: taxa de prenhez individual e consolidada, e uso de cada carneiro por estação de monta.
- **Lista de animais vazios** ao final do processo reprodutivo.
- **Exportação dos resultados** em Excel (múltiplas abas) e em relatório final em PDF.

## Estrutura de dados esperada

A planilha enviada precisa conter as seguintes colunas:

- `Ordem`, `Número de Identificação`
- `Diagnóstico de Gestação Inicial`
- `Estação de monta 1`, `Carneiro_monta_1`, `Diagnóstico de Gestação 1`
- `Estação de monta 2`, `Carneiro_monta_2`, `Diagnóstico de Gestação 2`
- `Estação de monta 3`, `Carneiro_monta_3`, `Diagnóstico de Gestação 3`
- `Diagnóstico de Gestação Final`

O arquivo `Modelo_Dados_Ovinos_IATF.xlsx`, disponível no próprio app, já traz essa estrutura pronta para preenchimento.

## Tecnologias

- [Streamlit](https://streamlit.io/) — interface web
- [pandas](https://pandas.pydata.org/) / [openpyxl](https://openpyxl.readthedocs.io/) / [xlrd](https://xlrd.readthedocs.io/) — leitura e manipulação dos dados
- [matplotlib](https://matplotlib.org/) — geração dos gráficos
- [ReportLab](https://www.reportlab.com/) — geração do relatório em PDF
- [NumPy](https://numpy.org/) — cálculos numéricos

## Como executar localmente

```bash
# Clonar o repositório
git clone https://github.com/biaposterli/PIBIC2026_Analise_Ovinos.git
cd PIBIC2026_Analise_Ovinos

# Instalar as dependências
pip install -r requirements.txt

# Rodar a aplicação
streamlit run app.py
```

A aplicação abrirá automaticamente no navegador (por padrão em `http://localhost:8501`).

## Como usar

1. Baixe o modelo de planilha disponível na barra lateral do app.
2. Preencha os dados reprodutivos dos animais, mantendo os nomes das colunas.
3. Envie a planilha preenchida pela barra lateral.
4. Navegue pelas abas (Visão Geral, Diagnósticos, Carneiros, Animais Vazios, Exportar) para consultar os resultados.
5. Baixe os resultados consolidados em Excel ou o relatório completo em PDF.

## Contexto

Projeto desenvolvido como parte do **PIBIC 2026** (Programa Institucional de Bolsas de Iniciação Científica), voltado à análise de indicadores reprodutivos em ovinocultura.
