import pandas as pd
import numpy as np
import streamlit as st
import os

URL_DATA = 'https://storage.dosm.gov.my/gdp/gdp_annual_nominal_supply.parquet'

df = pd.read_parquet(URL_DATA)
if 'date' in df.columns: df['date'] = pd.to_datetime(df['date'])

print(df)
