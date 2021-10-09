import xmltodict
import pandas as pd
import numpy as np
import collections

# File locations
anvisa_file = r"..\DataSources\data_anvisa.csv"
#drugbank_file = r"..\DataSources\full database.xml"    # Full DrugBank - Takes ~6 min to parse
drugbank_file = r"..\DataSources\drugbank_sample6.xml"  # Sample DrugBank with only 6 drugs
# Export
exp_csv_drugs = r"..\DataSources\exp_csv_drugs.csv"
exp_csv_interactions = r"..\DataSources\exp_csv_interactions.csv"
exp_csv_pAtivos = r"..\DataSources\exp_csv_pAtivos.csv"


# Importing Data Sources (AS-IS) - ANVISA
df_anvisa = pd.read_csv(anvisa_file, sep=';')
# Importing Data Sources (AS-IS) - DrugBank
with open(drugbank_file, encoding='utf-8') as fd:
    drugbank_dict = xmltodict.parse(fd.read())

# region DrugBank
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
            data.append([drugOrigin_id,
                         drugDestiny_id
                         ])
# This way impact negatively the negative
#            data.append({'drugbank-id1':drugOrigin_id,
#                         'drugbank-id2':drugDestiny_id
#                         })
        elif type(drugOrigin['drug-interactions']['drug-interaction']) == list:
            for drugDestiny in drugOrigin['drug-interactions']['drug-interaction']:
                drugDestiny_id = str(drugDestiny['drugbank-id'])
                data.append([drugOrigin_id,
                             drugDestiny_id
                             ])
#                data.append({'drugbank-id1':drugOrigin_id,
#                             'drugbank-id2':drugDestiny_id
#                             })

# Removing reversed duplicates
data = {tuple(sorted(item)) for item in data}
df_interactions = pd.DataFrame(data, columns=['drugbank-id1','drugbank-id2'])

# Exporting
df_drugs.to_csv(exp_csv_drugs, index = False)
df_interactions.to_csv(exp_csv_interactions, index = False)

# endregion DrugBank

# region ANVISA

# Names (Anvisa_Name)

s_Names = df_anvisa['NOME_PRODUTO']  # Series
s_Registry = df_anvisa['NUMERO_REGISTRO_PRODUTO']  
s_pAtivos = df_anvisa['PRINCIPIO_ATIVO']  

if len(s_Names) != len(s_Registry) or len(s_Names) != len(s_pAtivos): # test
    print('Unexpected error: Data Series s_names and s_Registry and s_pAtivos differ in length!')
    exit(1)

dictNames = dict()
listRegistry = list()
dictPrinciples = dict()
list_Names_Principles = list()
new_id_name = 0
new_id_principle = 0
for i in range(len(s_Names)):
    # Names & Registry
    name = str(s_Names[i]).strip().upper()
    if name not in dictNames:
        new_id_name += 1
        dictNames[name] = new_id_name
        listRegistry.extend([new_id_name, int(s_Registry[i])])
    else:
        listRegistry.extend([int(dictNames[name]), int(s_Registry[i])])

    # Extracting Active Principles
    rowStr = s_pAtivos[i]
    if type(rowStr)==str:
        principleList = list(map(str.upper,list(map(str.strip, rowStr.split('+')))))
        
        for principle in principleList:

            # Active Principles Entity (Keep Unicity)
            if principle not in dictPrinciples:
                new_id_principle += 1
                dictPrinciples[principle] = new_id_principle
                # Active Principles - Relation with Name
                list_Names_Principles.extend([int(dictNames[name]), new_id_principle]) # Here name is always on its dict
            else:
                list_Names_Principles.extend([int(dictNames[name]), int(dictPrinciples[principle])]) # Same
    else:
        continue # just ignore

# Exporting
ds_Anvisa_PrinciplesExp = pd.DataFrame(dictPrinciples.items(), columns=['nome_pAtivo','id_pAtivo'])
ds_Anvisa_PrinciplesExp.to_csv(exp_csv_pAtivos, encoding="utf-8", index = False)

# endregion


pass