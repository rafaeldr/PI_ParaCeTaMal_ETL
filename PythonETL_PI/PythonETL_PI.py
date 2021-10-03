import xmltodict
import pandas as pd
import numpy as np
import collections

# File locations
anvisa_file = r"..\DataSources\data_anvisa.csv"
drugbank_file = r"..\DataSources\full database.xml"    # Full DrugBank - Takes ~6 min to parse
#drugbank_file = r"..\DataSources\drugbank_sample6.xml"  # Sample DrugBank with only 6 drugs
exp_csv_drugs = r"..\DataSources\exp_csv_drugs.csv"
exp_csv_interactions = r"..\DataSources\exp_csv_interactions.csv"

# Importing Data Sources (AS-IS) - ANVISA
df_anvisa = pd.read_csv(anvisa_file, sep=';')
# Importing Data Sources (AS-IS) - DrugBank
with open(drugbank_file, encoding='utf-8') as fd:
    drugbank_dict = xmltodict.parse(fd.read())

# Drugs - Extraction
data = []
for drug in drugbank_dict['drugbank']['drug']:
    if type(drug['drugbank-id']) == list:
        id = str(drug['drugbank-id'][0]['#text'])
    else:
        id = str(drug['drugbank-id']['#text'])
    data.append({'drugbank-id':id,
                 'name':str(drug['name'])
                 })
df_drugs = pd.DataFrame(data)

# Interactions - Extraction
data = []
for drugOrigin in drugbank_dict['drugbank']['drug']:
    if type(drugOrigin['drugbank-id']) == list:
        drugOrigin_id = str(drugOrigin['drugbank-id'][0]['#text'])
    else:
        drugOrigin_id = str(drugOrigin['drugbank-id']['#text'])

    if drugOrigin['drug-interactions']!=None:
        if drugOrigin['drug-interactions']['drug-interaction'] == collections.OrderedDict: # only 1 registry
            drugDestiny_id = str(drugOrigin['drug-interactions']['drug-interaction']['drugbank-id'])
            data.append({'drugbank-id1':drugOrigin_id,
                         'drugbank-id2':drugDestiny_id
                         })
        elif type(drugOrigin['drug-interactions']['drug-interaction']) == list:
            for drugDestiny in drugOrigin['drug-interactions']['drug-interaction']:
                drugDestiny_id = str(drugDestiny['drugbank-id'])
                data.append({'drugbank-id1':drugOrigin_id,
                             'drugbank-id2':drugDestiny_id
                             })

df_interactions = pd.DataFrame(data)

# Exporting
df_drugs.to_csv(exp_csv_drugs, index = False)
df_interactions.to_csv(exp_csv_interactions, index = False)