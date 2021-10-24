import xmltodict
import pandas as pd
import numpy as np
import collections
import unidecode

# File locations
anvisa_file = r"..\DataSources\data_anvisa.csv"
#drugbank_file = r"..\DataSources\full database.xml"    # Full DrugBank - Takes ~6 min to parse
drugbank_file = r"..\DataSources\drugbank_sample6.xml"  # Sample DrugBank with only 6 drugs
# Export
exp_csv_drugs = r"..\DataSources\exp_csv_drugs.csv"
exp_csv_interactions = r"..\DataSources\exp_csv_interactions.csv"
exp_csv_pAtivos = r"..\DataSources\exp_csv_pAtivos.csv"
exp_csv_Nomes = r"..\DataSources\exp_csv_Nomes.csv"
exp_csv_Nomes_pAtivos = r"..\DataSources\exp_csv_Nomes_pAtivos.csv"

exp_csv_Analysis_Nomes_pAtivos = r"..\DataSources\exp_csv_Analysis_Nomes_pAtivos.csv"


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

dictNames = dict()                  # ANVISA Commercial Names
dictNamesAccented = dict()                  # Same WITH accentuation
listRegistry = list()               # ANVISA Registry Number (optional/debugging purposes)
dictPrinciples = dict()             # ANVISA Active Principles
dictPrinciplesAccented = dict()             # Same WITH accentuation
list_Names_Principles = list()      # ANVISA Relation (Commercial Names <--> Active Principles)
new_id_name = 0
new_id_principle = 0
for i in range(len(s_Names)):
    # Names & Registry
    name_accented = str(s_Names[i]).strip().upper()
    name_accented = " ".join(name_accented.split())  # Normalize White Spaces
    name = unidecode.unidecode(name_accented)
    if name not in dictNames:
        new_id_name += 1
        dictNames[name] = new_id_name
        dictNamesAccented[name_accented] = new_id_name
        listRegistry.append((new_id_name, int(s_Registry[i]))) # append tuple in a list (previous bug: "extend" flat the elements)
    else:
        listRegistry.append((int(dictNames[name]), int(s_Registry[i])))

    # Extracting Active Principles
    rowStr = s_pAtivos[i]
    if type(rowStr)==str:
        principleList = list(map(str.upper,list(map(str.strip, rowStr.split('+')))))
        
        for principle in principleList:
            principle = " ".join(principle.split())  # Normalize White Spaces
            principle_u = unidecode.unidecode(principle)
            # Active Principles Entity (Keep Unicity)
            if principle_u not in dictPrinciples:
                new_id_principle += 1
                dictPrinciples[principle_u] = new_id_principle
                dictPrinciplesAccented[principle] = new_id_principle
                # Active Principles - Relation with Name
                list_Names_Principles.append((int(dictNames[name]), new_id_principle)) # Here name is always on its dict  // Tuple inside List
            else:
                list_Names_Principles.append((int(dictNames[name]), int(dictPrinciples[principle_u]))) # Same
    else:
        continue # just ignore

# Exporting
ds_Anvisa_PrinciplesExp = pd.DataFrame(dictPrinciples.items(), columns=['nome_pAtivo','id_pAtivo'])
ds_Anvisa_PrinciplesExp.to_csv(exp_csv_pAtivos, encoding="utf-8", index = False)

ds_Anvisa_Names = pd.DataFrame(dictNames.items(), columns=['nomeProduto','id'])
ds_Anvisa_Names.to_csv(exp_csv_Nomes, encoding="utf-8", index = False)

ds_Anvisa_Names_Principles = pd.DataFrame(list_Names_Principles, columns=['idProduto','idPrincipio'])
ds_Anvisa_Names_Principles.to_csv(exp_csv_Nomes_pAtivos, encoding="utf-8", index = False)


# Search for Products With Exact Same Name of Action Principles (Analysis Task)
list_Equal_Names_Principles = list()
for nameStr in dictNames:
    
    nameStrList = list(map(str.upper,list(map(str.strip, nameStr.split('+')))))
    if len(nameStrList) == 1:
        # Case A : Product Name = 1 Active Principle    
        if nameStrList[0] in dictPrinciples:
            #list_Equal_Names_Principles.append((int(dictNames[nameStr]), nameStr, dictPrinciples[nameStrList[0]], nameStrList[0]))
            pass
    else:
        # Case B : Product Name = 2-More Active Principles
    
        if set(nameStrList).issubset(dictPrinciples):
            #list_Equal_Names_Principles.append((int(dictNames[nameStr]), nameStr))
            #print('exists')
            pass
        else:
            list_Equal_Names_Principles.append((int(dictNames[nameStr]), nameStr))
            pass

        #match_count = 0
        #for name in nameStrList:
        #    # One Product With Many Names = A candidate to list of known principles
        #    if name in dictPrinciples:
        #        match_count += 1
        #    pass
        #pass

    # Case *: Product Name is unique
    pass

ds_Equal_Names_Principles = pd.DataFrame(list_Equal_Names_Principles, columns=['idProduto','nomeProduto'])#,'idPrincipio','nomePrincipio'])
ds_Equal_Names_Principles.to_csv(exp_csv_Analysis_Nomes_pAtivos, encoding="utf-8", index = False)


# endregion


pass