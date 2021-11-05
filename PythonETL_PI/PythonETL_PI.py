import xmltodict
import pandas as pd
import numpy as np
import collections
import unidecode
import TranslationModule
import TermMatchingModule

# Parameters
callTranslator = False  # Keep false unless required (implies in costs from GoogleCloud)
callTermMatching = True # Keep false unless required (implies in high computation time)
prodEnvironment = False # False for "development/test"; true for "production" execution
silent = False          # Display track of progress info (when False)
TermMatchingModule.silent = silent
TranslationModule.silent = silent

# File locations
anvisa_file = r"..\DataSources\data_anvisa.csv"
if prodEnvironment:
    drugbank_file = r"..\DataSources\full database.xml"    # Full DrugBank - Takes ~6 min to parse
else:
    drugbank_file = r"..\DataSources\drugbank_sample6.xml"  # Sample DrugBank with only 6 drugs
# Export
exp_csv_drugs = r"..\DataSources\exp_csv_drugs.csv"
exp_csv_interactions = r"..\DataSources\exp_csv_interactions.csv"
exp_csv_pAtivos = r"..\DataSources\exp_csv_pAtivos.csv"
exp_csv_pAtivosAccented = r"..\DataSources\exp_csv_pAtivosAccented.csv"
exp_csv_Nomes = r"..\DataSources\exp_csv_Nomes.csv"
exp_csv_Nomes_pAtivos = r"..\DataSources\exp_csv_Nomes_pAtivos.csv"
exp_csv_pAtivos_Traducoes = r"..\DataSources\exp_csv_pAtivos_Traducoes.csv"
exp_csv_Analysis_Nomes_pAtivos = r"..\DataSources\exp_csv_Analysis_Nomes_pAtivos.csv" # Used for analysis
exp_csv_DrugBank_Anvisa = r"..\DataSources\exp_csv_DrugBank_Anvisa.csv"

# Importing Data Sources (AS-IS) - ANVISA
if not silent: print('Importing Data Sources (AS-IS) - ANVISA')
df_anvisa = pd.read_csv(anvisa_file, sep=';')
# Importing Data Sources (AS-IS) - DrugBank
if not silent: print('Importing Data Sources (AS-IS) - DrugBank') 
with open(drugbank_file, encoding='utf-8') as fd:
    drugbank_dict = xmltodict.parse(fd.read())

# region DrugBank
# Drugs - Extraction
if not silent: print('DrugBank - Extracting Names') 
data = []
for drug in drugbank_dict['drugbank']['drug']:
    if type(drug['drugbank-id']) == list:
        id = str(drug['drugbank-id'][0]['#text'])
    else:
        id = str(drug['drugbank-id']['#text'])
    id = id[2:] # Adjust ID to integer (not varchar/string)
    data.append({'drugbank-id':int(id),
                 'name':str(drug['name']).strip().upper()
                 })
df_drugs = pd.DataFrame(data)

# Interactions - Extraction
if not silent: print('DrugBank - Extracting Interactions') 
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
# Changed for execution time improvement
#            data.append({'drugbank-id1':drugOrigin_id,
#                         'drugbank-id2':drugDestiny_id})
        elif type(drugOrigin['drug-interactions']['drug-interaction']) == list:
            for drugDestiny in drugOrigin['drug-interactions']['drug-interaction']:
                drugDestiny_id = str(drugDestiny['drugbank-id'])
                data.append([drugOrigin_id,
                             drugDestiny_id
                             ])

# Removing reversed duplicates
if not silent: print('DrugBank - Interactions - Removing Reversed Duplicates') 
data = {tuple(sorted(item)) for item in data}
df_interactions = pd.DataFrame(data, columns=['drugbank-id1','drugbank-id2'])

# Exporting
if not silent: print('DrugBank - Exporting CSVs') 
df_drugs.to_csv(exp_csv_drugs, index = False)
df_interactions.to_csv(exp_csv_interactions, index = False)

# endregion DrugBank

# region ANVISA

# Names (Anvisa_Name)

s_Names = df_anvisa['NOME_PRODUTO']  # Series
s_Registry = df_anvisa['NUMERO_REGISTRO_PRODUTO']  
s_pAtivos = df_anvisa['PRINCIPIO_ATIVO']  

# Test
if len(s_Names) != len(s_Registry) or len(s_Names) != len(s_pAtivos):
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
    if not silent: print('ANVISA - Processing Names and Active Principles: '+str(i+1)+' of '+str(len(s_Names))+'\r', end="")
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
                if (int(dictNames[name]), int(dictPrinciples[principle_u])) not in list_Names_Principles:
                    list_Names_Principles.append((int(dictNames[name]), int(dictPrinciples[principle_u]))) # Same
    else:
        continue # just ignore
if not silent: print()


# Search for Products With Exact Same Name of Action Principles (Analysis Task)
list_Equal_Names_Principles = list()
for i in reversed(range(len(list(dictNames.keys())))): # Reversed cause size changes over iterations
    if not silent: print('ANVISA - Analyzing Names and Active Principles: (reversed) '+str(i+1)+' of '+str(len(list(dictNames.keys())))+'\r', end="")
    nameStr = list(dictNames.keys())[i]
    nameStrList = list(map(str.upper,list(map(str.strip, nameStr.split('+')))))
    if len(nameStrList) == 1:
        # Case A : Product Name = 1 Active Principle    
        if nameStrList[0] in dictPrinciples:

            idx_number = dictNames[nameStrList[0]]
            del dictNames[nameStrList[0]] # Step 1: Remove from dictNames
            key_value = list(dictNamesAccented.keys())[list(dictNamesAccented.values()).index(idx_number)] # Required since key_value can have different accentuation
            del dictNamesAccented[key_value] # Step 2: Remove from dictNamesAccented

            for item in list_Names_Principles:
                if item[0] == idx_number:
                    list_Names_Principles.remove(item)
    # Case B : Product Name = 2-More Active Principles
    elif set(nameStrList).issubset(dictPrinciples): # Only the case where ALL exists as principles
        idx_number = dictNames[nameStr] # original full name
        del dictNames[nameStr]  # remove Name (composed)
        key_value = list(dictNamesAccented.keys())[list(dictNamesAccented.values()).index(idx_number)] 
        del dictNamesAccented[key_value] 

        for item in list_Names_Principles:
            if item[0] == idx_number:       # Remember: Can be already removed during Case A?
                list_Names_Principles.remove(item)
    else:
        list_Equal_Names_Principles.append((int(dictNames[nameStr]), nameStr))  # No match (but multiple names)
if not silent: print()

# Manual Cleanup Section (after visual inspection)

if not silent: print('ANVISA - Executing Manual Cleanup Procedures') 
# 1. Renaming
dictPrinciples['HIDROBROMETO DE CITALOPRAM'] = dictPrinciples.pop('HIDROBROMETO DE CITALOPRAM (PORT. 344/98 LISTA C 1)')
dictPrinciplesAccented['HIDROBROMETO DE CITALOPRAM'] = dictPrinciplesAccented.pop('HIDROBROMETO DE CITALOPRAM (PORT. 344/98 LISTA C 1)')
dictPrinciples['OXANDROLONA'] = dictPrinciples.pop('OXANDROLONA (PORT. 344/98 LISTA C 5)')
dictPrinciplesAccented['OXANDROLONA'] = dictPrinciplesAccented.pop('OXANDROLONA (PORT. 344/98 LISTA C 5)')

# 2. Change Codes and Delete
change_dict = {3739 : 23, 2974 : 23, 1331 : 23, 1843 : 1873, 1299 : 639, 571 : 570,
               3872 : 2962, 1180 : 211, 2610 : 2450, 3404 : 1761, 1387 : 414, 2603 : 768, 
               2723 : 1994, 2561 : 17, 2727 : 311, 1974 : 19, 3561 : 105, 3821 : 105, 3210 : 2924, 
               3215 : 1239, 3782 : 169, 1837 : 37, 2928 : 20, 1424 : 20, 2716 : 1256, 3417 : 1256, 
               9 : 1265, 3061 : 1938, 1714 : 1487, 2607 : 416, 2040 : 501, 418 : 501, 3687 : 501, 
               2046 : 3397, 2350 : 2944}

change_list = [3739, 2974, 1331, 1843, 1299, 571, 3872, 1180, 2610, 3404,
               1387, 2603, 2723, 2561, 2727, 1974, 3561, 3821, 3210, 3215,
               3782, 1837, 2928, 1424, 2716, 3417, 9, 3061, 1714, 2607,
               2040, 418, 3687, 2046, 2350]

# Adjust relationship
for item in list_Names_Principles:
    if item[1] in change_list:
        item_temp = list(item)
        item_temp[1] = change_dict[item_temp[1]]
        item_temp = tuple(item_temp)
        list_Names_Principles.remove(item)
        list_Names_Principles.append(item_temp)

# Remove principle
for item in change_list:
    idx_number = item
    key_value = list(dictPrinciples.keys())[list(dictPrinciples.values()).index(idx_number)]
    del dictPrinciples[key_value]
    key_value = list(dictPrinciplesAccented.keys())[list(dictPrinciplesAccented.values()).index(idx_number)]
    del dictPrinciplesAccented[key_value] 

# 3. Just Delete
delete_list = [3954, 3878, 3867, 3823, 3799, 3727, 3472, 3396, 3348, 3284, 2751, 
               2742, 2665, 2562, 2418, 2156, 2115, 1977, 1739, 1610, 936, 632, 1281]

for item in delete_list:
    idx_number = item
    key_value = list(dictPrinciples.keys())[list(dictPrinciples.values()).index(idx_number)]
    del dictPrinciples[key_value]
    key_value = list(dictPrinciplesAccented.keys())[list(dictPrinciplesAccented.values()).index(idx_number)]
    del dictPrinciplesAccented[key_value] 

# Remove relationship
for item in list_Names_Principles:
    if item[1] in delete_list:
        list_Names_Principles.remove(item)


# Prepare DataFrames
if not silent: print('ANVISA - Creating DataFrames') 
df_Anvisa_PrinciplesAccented = pd.DataFrame(dictPrinciplesAccented.items(), columns=['nome_pAtivo','id_pAtivo'])
df_Anvisa_Principles = pd.DataFrame(dictPrinciples.items(), columns=['nome_pAtivo','id_pAtivo'])
df_Anvisa_Names = pd.DataFrame(dictNames.items(), columns=['nomeProduto','id'])
df_Anvisa_Names_Principles = pd.DataFrame(list_Names_Principles, columns=['idProduto','idPrincipio'])
df_Equal_Names_Principles = pd.DataFrame(list_Equal_Names_Principles, columns=['idProduto','nomeProduto'])

# Translation Section Call (Run Once) - "Limited Resource" [Google Translator API]
if callTranslator:
    if not silent: print('ANVISA - Calling Translation Module') 
    s_pAtivos = df_Anvisa_PrinciplesAccented['nome_pAtivo']  # Series
    s_pAtivosTranslated = TranslationModule.BatchTranslate(s_pAtivos)
    s_pAtivosTranslated.to_csv(exp_csv_pAtivos_Traducoes, index = False)
    df_PrinciplesTraducoes = s_pAtivosTranslated
else:
    if not silent: print('ANVISA - Loading Translations') 
    df_PrinciplesTraducoes = pd.read_csv(exp_csv_pAtivos_Traducoes, sep=',')

# Test
if len(df_Anvisa_PrinciplesAccented) != len(df_PrinciplesTraducoes):
    print("Unexpected error: Dataframes doesn't match in length! Translations failed or data changed shape since last batch translation.")
    exit(1)

# Adjust DataFrames
df_Anvisa_PrinciplesAccented['translated_pAtivo'] = df_PrinciplesTraducoes
df_Anvisa_Principles['translated_pAtivo'] = df_PrinciplesTraducoes

# Export DataFrames
if not silent: print('ANVISA - Exporting CSVs')
df_Anvisa_PrinciplesAccented.to_csv(exp_csv_pAtivosAccented, encoding="utf-8", index = False)
df_Anvisa_Principles.to_csv(exp_csv_pAtivos, encoding="utf-8", index = False)
df_Anvisa_Names.to_csv(exp_csv_Nomes, encoding="utf-8", index = False)
df_Anvisa_Names_Principles.to_csv(exp_csv_Nomes_pAtivos, encoding="utf-8", index = False)
df_Equal_Names_Principles.to_csv(exp_csv_Analysis_Nomes_pAtivos, encoding="utf-8", index = False)

# endregion

# Nomenclature Pair Matching Module Call
if callTermMatching:
    if not silent: print('DrugBank + ANVISA - Calling Term Matching Module')
    df_DrugBank_Anvisa = TermMatchingModule.match(df_drugs['name'], df_drugs['drugbank-id'], df_Anvisa_PrinciplesAccented['translated_pAtivo'], df_Anvisa_PrinciplesAccented['id_pAtivo'])
    df_DrugBank_Anvisa.to_csv(exp_csv_DrugBank_Anvisa, index = False)
else:
    if not silent: print('ANVISA - Loading Preprocessed Term Matching') 
    df_DrugBank_Anvisa = pd.read_csv(exp_csv_DrugBank_Anvisa, sep=',')

print()

pass