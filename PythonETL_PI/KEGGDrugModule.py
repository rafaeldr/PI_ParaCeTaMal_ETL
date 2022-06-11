import pandas as pd
import numpy as np


# Parameters
silent = False
threshold = 0

# File locations
file = r"..\DataSources\drug"

drugID = -1
entryCount = endCount = lineCount = 0
drugs = []

# Iterate Through File: Line by Line
with open(file) as f:
	for line in f:
		lineCount = lineCount + 1 # For DEBUG
		tokens = list(map(str.strip, line.split()))
		
		# Closing Atual Drug Entry
		if tokens[0] == '///':
			endCount = endCount + 1
			# RESET
			drugID = -1
			if check == True:
				print('')
				pass # Drugs without name (e.g. D09853, line 597659)
			continue # Skip checks

		# New Drug Entry
		if tokens[0] == 'ENTRY':
			entryCount = entryCount + 1
			drugID = int(tokens[1][1:])
			check = True
		elif tokens[0] == 'NAME':
			check = False
			drugName = tokens[1].upper()
			naming_candidates = tokens[2:] # Discard the trivial single name already included
			for candidate in naming_candidates:
				if candidate[0] == '(' or candidate[0] == ';': # Discard codes or other non-name stuff
					break
				else:
					drugName = drugName + ' ' + candidate.replace(',', ' ').strip().upper()
			drugs.append({'keggdrug-id':drugID,
					     'name':drugName
						})

# Integrity Check
if(entryCount != endCount):
	print('Unexpected error: KEGG Drug Data : Entry codes and end codes doesn`t match!')
	exit(1)

print('end')

