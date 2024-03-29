# -*- coding: utf-8 -*-
"""Profissao Analista de dados M28 Exercicio.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vceR-poL7BeSDZay3d6KKbE9WAzdSXcI

<img src="https://raw.githubusercontent.com/andre-marcos-perez/ebac-course-utils/main/media/logo/newebac_logo_black_half.png" alt="ebac-logo">

---

# **Módulo** | Análise de Dados: COVID-19 Dashboard
Professor [André Perez](https://www.linkedin.com/in/andremarcosperez/)

---

# **Tópicos**

<ol type="1">
  <li>Contexto;</li>
  <li>Pacotes;</li>
  <li>Extração e Manipulação;</li>
  <li>Carregamento.</li>
</ol>

---

# **COVID Dashboard**

## 1\. Contexto

## 1.1. TLDR (TOO LONG DIDN'T READ)

- **Dashboard**:
  - Google Data Studio ([link](https://lookerstudio.google.com/reporting/247ff03f-ba36-431f-91c4-1aefd32bcedf)).
 - **Fontes**:
  - Casos pela universidade John Hopkins ([link](https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_daily_reports));
  - Vacinação pela universidade de Oxford ([link](https://covid.ourworldindata.org/data/owid-covid-data.csv)).

### **1.2. Pandemia Coronavírus**

> A COVID-19 é uma doença infecciosa que afeta principalmente o sistema respiratório e é causada pelo vírus conhecido como SARS-CoV-2. Esta doença apresenta um potencial grave devido à sua capacidade de causar complicações sérias, sendo altamente contagiosa e com uma disseminação ampla em todo o mundo. De acordo com informações disponibilizadas pelo Governo brasileiro ([link](https://www.gov.br/saude/pt-br/coronavirus/o-que-e-o-coronavirus)), a COVID-19 representa uma preocupação significativa devido à sua propagação rápida e aos riscos que apresenta para a saúde pública, exigindo medidas rigorosas de prevenção e controle para mitigar seus impactos.

A existência de informações atualizadas e detalhadas sobre a progressão da pandemia ao longo do tempo em uma região específica é crucial para implementar estratégias eficazes de contenção. Este projeto tem como objetivo desenvolver um painel de controle interativo que permita explorar e visualizar dados sobre a evolução dos casos de COVID-19 e o progresso da vacinação no Brasil. Através dessa ferramenta, será possível analisar de forma mais profunda e dinâmica os padrões e tendências relacionados à pandemia, auxiliando na tomada de decisões e no monitoramento contínuo da situação epidemiológica do país.

## 2\. Pacotes e bibliotecas
"""

import math
from typing import Iterator
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

"""## 3\. Extração e Manipulação

### 3.1 Coleta dos dados de infecções e mortes

O dashboard terá os dados a partir de 2021 até o último registro de dados encontrado, que é do dia 10/03/2023.
"""

def date_range(start_date: datetime, end_date: datetime) -> Iterator[datetime]:
  date_range_days: int = (end_date - start_date).days
  for lag in range(date_range_days):
    yield start_date + timedelta(lag)

start_date = datetime(2021,  1,  1)
end_date   = datetime(2023, 3, 10)

cases = []

for date in date_range(start_date=start_date, end_date=end_date):
    date_str = date.strftime('%m-%d-%Y')
    data_source_url = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{date_str}.csv'

    case = pd.read_csv(data_source_url, sep=',')

    case = case.drop(['FIPS', 'Admin2', 'Last_Update', 'Lat', 'Long_', 'Recovered', 'Active', 'Combined_Key', 'Case_Fatality_Ratio'], axis=1)
    case = case.query('Country_Region == "Brazil"').reset_index(drop=True)
    case['Date'] = pd.to_datetime(date.strftime('%Y-%m-%d'))

    cases.append(case)

cases = pd.concat(cases, ignore_index=True)

cases.head()

"""### 3.2 Preparação dos dados de infecção e mortes para o dashboard

Renomeando as colunas...
"""

cases = cases.rename(
  columns={
    'Province_State': 'state',
    'Country_Region': 'country'
  }
)

for col in cases.columns:
  cases = cases.rename(columns={col: col.lower()})

"""Ajustamos o nome dos estados..."""

states_map = {
    'Amapa': 'Amapá',
    'Ceara': 'Ceará',
    'Espirito Santo': 'Espírito Santo',
    'Goias': 'Goiás',
    'Para': 'Pará',
    'Paraiba': 'Paraíba',
    'Parana': 'Paraná',
    'Piaui': 'Piauí',
    'Rondonia': 'Rondônia',
    'Sao Paulo': 'São Paulo'
}

cases['state'] = cases['state'].apply(lambda state: states_map.get(state) if state in states_map.keys() else state)

"""Adicionando novas colunas..."""

# Quantias por mês e ano

cases['month'] = cases['date'].apply(lambda date: date.strftime('%Y-%m'))
cases['year']  = cases['date'].apply(lambda date: date.strftime('%Y'))

# População por estado

cases['population'] = round(100000 * (cases['confirmed'] / cases['incident_rate']))
cases = cases.drop('incident_rate', axis=1)

# Número, média móvel (7 dias) e estabilidade (14 dias) de casos e mortes por estado

cases_ = None
cases_is_empty = True

def get_trend(rate: float) -> str:

  if np.isnan(rate):
    return np.NaN

  if rate < 0.75:
    status = 'downward'
  elif rate > 1.15:
    status = 'upward'
  else:
    status = 'stable'

  return status


for state in cases['state'].drop_duplicates():

  cases_per_state = cases.query(f'state == "{state}"').reset_index(drop=True)
  cases_per_state = cases_per_state.sort_values(by=['date'])

  cases_per_state['confirmed_1d'] = cases_per_state['confirmed'].diff(periods=1)
  cases_per_state['confirmed_moving_avg_7d'] = np.ceil(cases_per_state['confirmed_1d'].rolling(window=7).mean())
  cases_per_state['confirmed_moving_avg_7d_rate_14d'] = (cases_per_state['confirmed_moving_avg_7d'] / cases_per_state['confirmed_moving_avg_7d'].shift(periods=14)).round(2)
  cases_per_state['confirmed_trend'] = cases_per_state['confirmed_moving_avg_7d_rate_14d'].apply(get_trend)

  cases_per_state['deaths_1d'] = cases_per_state['deaths'].diff(periods=1)
  cases_per_state['deaths_moving_avg_7d'] = np.ceil(cases_per_state['deaths_1d'].rolling(window=7).mean())
  cases_per_state['deaths_moving_avg_7d_rate_14d'] = cases_per_state['deaths_moving_avg_7d']/cases_per_state['deaths_moving_avg_7d'].shift(periods=14)
  cases_per_state['deaths_moving_avg_7d_rate_14d'] = cases_per_state['deaths_moving_avg_7d_rate_14d'].round(2)
  cases_per_state['deaths_trend'] = cases_per_state['deaths_moving_avg_7d_rate_14d'].apply(get_trend)

  if cases_is_empty:
    cases_ = cases_per_state
    cases_is_empty = False
  else:
    cases_ = cases_.append(cases_per_state, ignore_index=True)

cases = cases_
cases_ = None

"""Realizando o type casting das colunas..."""

cases['population'] = cases['population'].astype('Int64')
cases['confirmed_1d'] = cases['confirmed_1d'].astype('Int64')
cases['confirmed_moving_avg_7d'] = cases['confirmed_moving_avg_7d'].astype('Int64')
cases['deaths_1d'] = cases['deaths_1d'].astype('Int64')
cases['deaths_moving_avg_7d'] = cases['deaths_moving_avg_7d'].astype('Int64')

"""Organizando as colunas..."""

cases = cases[['date', 'country', 'state', 'population', 'confirmed', 'confirmed_1d', 'confirmed_moving_avg_7d', 'confirmed_moving_avg_7d_rate_14d', 'confirmed_trend', 'deaths', 'deaths_1d', 'deaths_moving_avg_7d', 'deaths_moving_avg_7d_rate_14d', 'deaths_trend', 'month', 'year']]

"""### 3.3 Coleta dos dados de vacinação"""

vaccines = pd.read_csv('https://covid.ourworldindata.org/data/owid-covid-data.csv', sep=',', parse_dates=[3], infer_datetime_format=True)

"""Separando os dados brasileiros..."""

vaccines = vaccines.query('location == "Brazil"').reset_index(drop=True)
vaccines = vaccines[['location', 'population', 'total_vaccinations', 'people_vaccinated', 'people_fully_vaccinated', 'total_boosters', 'date']]

vaccines.head()

vaccines.info()

"""### 3.4 Preparação dos dados de vacinação para o dashboard

Preenchendo os dados faltantes com o valor anterior mais próximo.
"""

vaccines = vaccines.fillna(method='ffill')

"""  Filtrando a base de dados de acordo com a coluna date para garantir que ambas as bases de dados tratam do mesmo período de tempo."""

vaccines = vaccines[(vaccines['date'] >= '2021-01-01') & (vaccines['date'] <= '2023-03-10')].reset_index(drop=True)

"""Ajustando o nome das colunas..."""

vaccines = vaccines.rename(
  columns={
    'location': 'country',
    'total_vaccinations': 'total',
    'people_vaccinated': 'one_shot',
    'people_fully_vaccinated': 'two_shots',
    'total_boosters': 'three_shots',
  }
)

"""Adicionando novas colunas..."""

# Valores por mês e ano

vaccines['month'] = vaccines['date'].apply(lambda date: date.strftime('%Y-%m'))
vaccines['year']  = vaccines['date'].apply(lambda date: date.strftime('%Y'))

# Porcentagens de primeira, segunda e a dose de reforço

vaccines['one_shot_perc'] = round(vaccines['one_shot'] / vaccines['population'], 4)
vaccines['two_shots_perc'] = round(vaccines['two_shots'] / vaccines['population'], 4)
vaccines['three_shots_perc'] = round(vaccines['three_shots'] / vaccines['population'], 4)

"""Fazendo o type casting das colunas..."""

vaccines['population'] = vaccines['population'].astype('Int64')
vaccines['total'] = vaccines['total'].astype('Int64')
vaccines['one_shot'] = vaccines['one_shot'].astype('Int64')
vaccines['two_shots'] = vaccines['two_shots'].astype('Int64')
vaccines['three_shots'] = vaccines['three_shots'].astype('Int64')

"""Organizando as colunas..."""

vaccines = vaccines[['date', 'country', 'population', 'total', 'one_shot', 'one_shot_perc', 'two_shots', 'two_shots_perc', 'three_shots', 'three_shots_perc', 'month', 'year']]

"""## 4\. Carregamento

Transformando os dataframes em arquivos excel.
"""

cases.to_excel('./covid-cases.xlsx', index=False)
vaccines.to_excel('./covid-vaccines.xlsx', index=False)