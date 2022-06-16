import pandas as pd
import numpy as np


# Parameters
silent = False
threshold = 0
# File locations
file = r"..\DataSources\drug"


def importKEGGDrug():

	drugID = -1
	entryCount = endCount = lineCount = 0	
	drugs = []
	drugsSynonyms = []
	drugMetabolicInteraction = []  # DrugID, HSA Code

	# Importing Data Sources - KEGG Drug
	if not silent: print('Importing Data Sources - KEGG Drug')
	# Iterate Through File: Line by Line
	with open(file) as f:
		for line in f:
			lineCount = lineCount + 1 # For DEBUG
			if not silent: print('KEGG Drug - Processing Line Number: '+str(lineCount)+' \r', end="")
			tokens = list(map(str.strip, line.split()))
		
			# Closing Atual Drug Entry
			if tokens[0] == '///':
				endCount = endCount + 1
				# RESET
				drugID = -1
				if checkName == True:
					pass # Drugs without name (e.g. D09853, line 597659)
				continue # Skip checks

			# Is a New Command?
			isCommandLine = True if line[0] != ' ' else False
			lastCommand = tokens[0] if isCommandLine else lastCommand

			# New Drug Entry
			if tokens[0] == 'ENTRY':
				entryCount = entryCount + 1
				drugID = int(tokens[1][1:])
				checkName = True
			elif tokens[0] == 'NAME':
				checkName = False
				drugName = tokens[1].upper()
				naming_candidates = tokens[2:] # Discard the trivial single name already included
				for candidate in naming_candidates:
					if candidate[0] == '(' or candidate[0] == ';': # Discard codes or other non-name stuff
						break
					else:
						drugName = drugName + ' ' + candidate.replace(',', '').strip().upper()
				drugs.append({'keggdrug-id':drugID,
							 'name':drugName.replace(';', '')
							})
			elif lastCommand == 'NAME':	# Only Synonyms
				drugName = tokens[0].upper()
				naming_candidates = tokens[1:] # Discard the trivial single name already included
				for candidate in naming_candidates:
					if candidate[0] == '(' or candidate[0] == ';': # Discard codes or other non-name stuff
						break
					else:
						drugName = drugName + ' ' + candidate.replace(',', '').strip().upper()
				drugsSynonyms.append({'keggdrug-id':drugID,
							 'name':drugName.replace(';', '')
							})
				pass
			elif tokens[0] == 'METABOLISM' or lastCommand == 'METABOLISM' or tokens[0] == 'INTERACTION' or lastCommand == 'INTERACTION':
				if isCommandLine:
					naming_candidates = tokens[1:]
				else:
					naming_candidates = tokens[0:]

				pending = False
				for candidate in naming_candidates:
					if candidate[0] == '[' or pending:
						first = True if (candidate[0] == '[') else False
						idx = candidate.find(']')
						pending = True if (idx == -1) else False
					
						if first:
							hsaCode = candidate[5:].replace(';', '').replace(',', '').replace(']', '').strip().upper()
						else:
							hsaCode = candidate.replace(';', '').replace(',', '').replace(']', '').strip().upper()
					
						# Convert and Check (can raise errors)
						hsaCode = int(hsaCode)

						drugMetabolicInteraction.append({'keggdrug-id':drugID,
									 'hsaCode':hsaCode
									})
		if not silent: print()

	# Integrity Check
	if(entryCount != endCount):
		print('Unexpected error: KEGG Drug Data : Entry codes and end codes doesn`t match!')
		exit(1)

	df_drugs = pd.DataFrame(drugs)
	df_drugsSynonyms = pd.DataFrame(drugsSynonyms)
	df_metabolic = pd.DataFrame(drugMetabolicInteraction)
	df_metabolic = df_metabolic.drop_duplicates()

	# Drugs Names Synonyms (Concat)
	df_drugsSynonyms = pd.concat([df_drugs, df_drugsSynonyms], ignore_index=True)
	df_drugsSynonyms = df_drugsSynonyms.drop_duplicates()

	# Cross Checking Drugs for Interaction 
	if not silent: print('Cross Checking Drugs for Interaction')

	drugDrugInteraction = [] # DrugID, DrugID
	#drugsSeries = df_drugs['keggdrug-id']

	# Subset of Drugs that Have Metabolic/Interaction Info
	drugsSeries = df_metabolic['keggdrug-id'].drop_duplicates()
	drugsSeries.reset_index(inplace=True, drop=True)

	# Searching for pair of interactions
	for i in range(len(drugsSeries)):
		for j in range(i+1,len(drugsSeries)):
		
			if not silent: print('Checking KEGG Interaction between: '+str(i)+' and '+str(j)+' of a total of '+str(len(drugsSeries))+'\r', end="")

			setA = set(list(df_metabolic[df_metabolic['keggdrug-id']==drugsSeries[i]]['hsaCode']))
			setB = set(list(df_metabolic[df_metabolic['keggdrug-id']==drugsSeries[j]]['hsaCode']))
			set_intersec = setA.intersection(setB)

			if len(set_intersec)>0:
				# Observe that j>i always
				drugDrugInteraction.append([int(drugsSeries[i]),
				 int(drugsSeries[j])
				 ])
		if not silent: print()

	# Check for Reversed Duplicates
	data = {tuple(sorted(item)) for item in drugDrugInteraction}
	if len(data) != len(drugDrugInteraction):
		print('Unexpected error: KEGG Drug Data : Found duplicate interactions!')
		exit(1)

	df_interaction = pd.DataFrame(data, columns=['keggdrug-id1','keggdrug-id2'])

	# Test Constraint id1 < id2 always
	if any(df_interaction['keggdrug-id1']>df_interaction['keggdrug-id2']):
		print('Unexpected error: KEGG Drug Data : Interactions should respect id1 < id2!')
		exit(1)

	return df_drugs, df_drugsSynonyms, df_interaction