# Análise Reproduutiva de Ovinos

Aplicação web (Streamlit) para análise de dados reprodutivos de ovinos submetidos a
protocolos de reprodução assistida com múltiplas estações de monta, desenvolvida no
âmbito de um projeto PIBIC.

O usuário define a quantidade de estações de monta do seu manejo, envia uma planilha
Excel preenchida com os dados dos animais e recebe automaticamente indicadores,
gráficos e um relatório final em PDF.

## Funcionalidades

- **Quantidade de estações de monta configurável**: o usuário escolhe, na barra
  lateral, quantas estações de monta (rodadas de cobertura) o seu manejo utiliza —
  de 1 até qualquer quantidade, sem limite máximo.
- **Download do modelo de planilha**, gerado automaticamente com a estrutura de
  colunas correspondente à quantidade de estações escolhida.
- **Upload e validação** da planilha preenchida, com checagem das colunas
  obrigatórias para a quantidade de estações informada.
- **Indicadores (KPIs)**: total de animais, número de carneiros, taxa de prenhez
  final e número de fêmeas vazias.
- **Análise por estação de monta** (quantas o usuário definir): animais submetidos,
  diagnósticos válidos, prenhes, vazias e taxa de prenhez, com gráficos de barras e
  pizza.
- **Diagnósticos de gestação por etapa** (inicial, cada estação de monta e final),
  detalhados em tabelas e gráficos.
- **Desempenho por carneiro**: taxa de prenhez individual e consolidada, e uso de
  cada carneiro por estação de monta.
- **Lista de animais vazios** ao final do processo reprodutivo.
- **Exportação dos resultados** em Excel (múltiplas abas) e em relatório final em PDF.

## Estrutura de dados esperada

A quantidade de colunas referentes às estações de monta depende da quantidade
escolhida pelo usuário na barra lateral do app (1, 2, 3, ... N). Para cada estação
`i`, a planilha precisa conter:

- `Estação de monta i`, `Carneiro_monta_i`, `Diagnóstico de Gestação i`

Além disso, a planilha precisa conter as colunas fixas:

- `Ordem`, `Número de Identificação`
- `Diagnóstico de Gestação Inicial`
- `Diagnóstico de Gestação Final`

O modelo de planilha é gerado automaticamente pelo próprio app, de acordo com a
quantidade de estações de monta escolhida na barra lateral, já trazendo a estrutura
de colunas correspondente pronta para preenchimento.

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

1. Escolha, na barra lateral, a quantidade de estações de monta do seu manejo.
2. Baixe o modelo de planilha gerado automaticamente para essa quantidade de estações.
3. Preencha os dados reprodutivos dos animais, mantendo os nomes das colunas.
4. Envie a planilha preenchida pela barra lateral.
5. Navegue pelas abas (Visão Geral, Diagnósticos, Carneiros, Animais Vazios, Exportar) para consultar os resultados.
6. Baixe os resultados consolidados em Excel ou o relatório completo em PDF.

## Contexto

Projeto desenvolvido como parte do **PIBIC 2026** (Programa Institucional de Bolsas de
Iniciação Científica), voltado à análise de indicadores reprodutivos em ovinocultura.
