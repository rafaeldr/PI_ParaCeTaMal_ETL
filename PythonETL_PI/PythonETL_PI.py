import xmltodict
import pandas as pd
import numpy as np

df=pd.read_csv('..\DataSources\data_anvisa.csv', sep=';')

with open(r"..\DataSources\full database.xml", encoding='utf-8') as fd:
    doc = xmltodict.parse(fd.read())