import pandas as pd
import numpy as np
import collections
from typing import List

# Parameters
silent = False
threshold = 0

def match(data1_Names : pd.Series, data1_Ids : pd.Series, data2_Names : pd.Series, data2_Ids : pd.Series) -> pd.DataFrame:
	
	# Conceptually: Cross Matrix
	# Implications -> NOT Symmetric
	# Practically: Iterate to find best (less costly to memory)
	
	# Test
	if len(data1_Names) != len(data1_Ids) or len(data2_Names) != len(data2_Ids):
		print('Unexpected error: Data Series passed for term matching module does not match in length!')
		exit(1)
	
	returnDataFrame = []
	toBeDeleted_FromData1 = []
	toBeDeleted_FromData2 = []

	# PASS1 -> Check Trivial Case and Remove At the End
	# This pass can remove abrupt computational time on next pass (expected)
	# (Avoiding tokenization procedures for perfect matches)
	for i in range(len(data1_Names)):
		if not silent: print('Processing Term Matching [PASS 1]: '+str(i+1)+' of '+str(len(data1_Names))+'\r', end="")
		for j in range(len(data2_Names)):
			# Case 1 - Trivial // Identical Strings
			# (Premisse: There is only 1 possible; since names are unique) => FALSE
			# But it can be controled, and the removal of matching pair (from origin) 
			# will be done at the end of PASS 1
			if(data1_Names[i]==data2_Names[j]): #Assuming they come: upper() and strip()
				# Include 'match'
				returnDataFrame.append([data1_Ids[i],
									 data1_Names[i],
									 data2_Ids[j],
									 data2_Names[j],
									 1])
				if i not in toBeDeleted_FromData1: toBeDeleted_FromData1.append(i)
				if j not in toBeDeleted_FromData2: toBeDeleted_FromData2.append(j)
				# break
	if not silent: print()

	if not silent: print('Term Matching [PASS 1]: '+str(len(returnDataFrame))+' matches found.')
	# Remove Paired Terms on Pass 1 before Pass 2
	data1_Ids = data1_Ids.drop(toBeDeleted_FromData1)
	data1_Ids.reset_index(inplace=True, drop=True)
	data1_Names = data1_Names.drop(toBeDeleted_FromData1)
	data1_Names.reset_index(inplace=True, drop=True)
	data2_Ids = data2_Ids.drop(toBeDeleted_FromData2)
	data2_Ids.reset_index(inplace=True, drop=True)
	data2_Names = data2_Names.drop(toBeDeleted_FromData2)
	data2_Names.reset_index(inplace=True, drop=True)
	toBeDeleted_FromData1 = toBeDeleted_FromData2 = []

	# Results Structure
	resultsVector = [0] * len(data1_Names)
	indexVector = [-1] * len(data1_Names)

	# PASS2 -> Iterate Cheking - Tokens
	for i in range(len(data1_Names)):

		if not silent: print('Processing Term Matching [PASS 2]: '+str(i+1)+' of '+str(len(data1_Names))+'\r', end="")
		i_tokens = list(map(str.strip, str(data1_Names[i]).replace('-', ' ').replace('+', ' ').replace(',', ' ').split()))

		# Check & remove 'empty' tokens
		for token in reversed(i_tokens):
			if len(token) == 0:
				i_tokens.remove(token)

		candidatesVector = [0] * len(data2_Names) 

		for j in range(len(data2_Names)):

			j_tokens = list(map(str.strip, str(data2_Names[j]).replace('-', ' ').replace('+', ' ').replace(',', ' ').split()))

			# Check & remove 'empty' tokens
			for token in reversed(j_tokens):
				if len(token) == 0:
					j_tokens.remove(token)

			# Tokenized Search
			candidatesVector[j] = tokenizedMatch(i_tokens, j_tokens)
			#candidatesVector[j] = candidatesVector[j]/len(data1_Names[i]) if (data1_Names[i]>data2_Names[j]) else candidatesVector[j]/len(data2_Names[j])
		
		# Set results (local indexes)
		resultsVector[i] = max(candidatesVector)
		indexVector[i] = max(range(len(candidatesVector)), key=candidatesVector.__getitem__)

		# Prepare Results for Function RETURN
		
		# Translate i/j indexes to ids
		# DrugBank id | ANVISA Principle id | Value
		# Considering Threshold
		if resultsVector[i] >= threshold:
			returnDataFrame.append([data1_Ids[i],
									data1_Names[i],
									data2_Ids[indexVector[i]],
									data2_Names[indexVector[i]],
									resultsVector[i]])
		
	if not silent: print()	

	df_return = pd.DataFrame(returnDataFrame, columns=['id_pAtivo','name_anvisa','drugbank-id','name_drugbank','matchingValue'])

	return df_return


# Break names into tokens and try to find best match value
def tokenizedMatch(names1 : List[str], names2 : List[str]) -> float:
	# here values are set by str len (normalized to 0..1 interval only at the end)

	finalScore = 0

	# Calculate Lengths
	sumLength1 = 0
	sumLength2 = 0
	for token in names1:
		sumLength1 += len(token)
	for token in names2:
		sumLength2 += len(token)

	sumLength = sumLength1 if (sumLength1 > sumLength2) else sumLength2

	# Array to keep results -> So we can chech BEST arrangement
	valuesMatrix = np.zeros((len(names1), len(names2)), dtype=int)
	valuesMatrixNormalized = np.zeros((len(names1), len(names2)), dtype=float)
	valuesMatrixTokenLength = np.zeros((len(names1), len(names2)), dtype=int)

	for i in range(len(names1)):
		tokenL1 = names1[i]
		bestPair = 0

		if len(tokenL1)==0:
			continue #skip

		for j in range(len(names2)):
			tokenL2 = names2[j]

			if len(tokenL2)==0:
				continue #skip

			if(tokenL1==tokenL2): # Best possible
				valuesMatrix[i,j] = len(tokenL1) # Same length
				valuesMatrixNormalized[i,j] = 1
				valuesMatrixTokenLength[i,j] = len(tokenL1) if (len(tokenL1) > len(tokenL2)) else len(tokenL2)
				continue
			value = strMatchShift(tokenL1,tokenL2)
			valuesMatrix[i,j] = value
			valuesMatrixTokenLength[i,j] = len(tokenL1) if (len(tokenL1) > len(tokenL2)) else len(tokenL2)
			valuesMatrixNormalized[i,j] = value/valuesMatrixTokenLength[i,j]

	# Choose best arrangement
	numTokens = min(len(names1), len(names2))

	for _ in range(numTokens):

		# Pick Global Max (Normalized) Value
		ind = np.unravel_index(np.argmax(valuesMatrixNormalized, axis=None), valuesMatrixNormalized.shape)

		finalScore += valuesMatrix[ind]
		#sumLength += (valuesMatrix[ind]/valuesMatrixNormalized[ind]) # Recover length arithmetically | Can Divide by Zero -> Generating 'nan' & Warning
		#sumLength += valuesMatrixTokenLength[ind]

		# Zeros on its line and column
		valuesMatrixNormalized[ind[0],:] = 0
		valuesMatrixNormalized[:,ind[1]] = 0
		valuesMatrix[ind[0],:] = 0 # Bug was here
		valuesMatrix[:,ind[1]] = 0
		# Repeat MIN times

	finalScore = finalScore/sumLength
	
	return finalScore


def strMatchShift(str1 : str, str2 : str) -> int:
	bestPair = 0

	if len(str1)<len(str2):
		small = str1
		large = str2
	else:
		small = str2
		large = str1

	# Start Phase
	# Vary Small in Size : |<-
	init = len(small)-1
	while init >= 0:
		subSmall = small[init:]
		init -= 1
		value = strMatch(subSmall,large)
		bestPair = value if (value > bestPair) else bestPair

	# Fixate the large / slide the small : ->|
	for startPointer in range(len(large)):
		
		subLarge = large[startPointer:]
		#maxlen = len(subLarge)
		#subSmall = small[0:maxlen] # Not required (func strMatch deal with it)	
		
		value = strMatch(subLarge, subSmall)
		bestPair = value if (value > bestPair) else bestPair
	
	return bestPair


def strMatch(str1 : str, str2 : str) -> int:

	# This is the simples function
	# Force same size comparison
	# Both starting at first char and only
	if len(str1) > len(str2):
		str1 = str1[0:len(str2)]
	else:
		str2 = str2[0:len(str1)]

	# Test
	if len(str1) != len(str2):
		print('Unexpected error: strMatch function expects string with same length!')
		exit(1)

	charMatch = 0
	for i in range(len(str1)):
		if str1[i]==str2[i]:
			charMatch += 1
	#print(str1+' '+str2+' '+str(charMatch)) # DEBUG

	return charMatch


# Test section

#df_DrugBank_Anvisa = TermMatchingModule.match()
#d = {'translated_pAtivo': ['PROLINE'], 'id_pAtivo': [1]}
#df1 = pd.DataFrame(data=d)
#d = {'name': ['BETAMEPRODINE'], 'drugbank-id': [31]}
#df2 = pd.DataFrame(data=d)
#df_DrugBank_Anvisa = match(df1['translated_pAtivo'], df1['id_pAtivo'], df2['name'], df2['drugbank-id'])