import pandas as pd
import numpy as np
import collections

import six
from google.cloud import translate_v2 as translate

import os
parentDir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(parentDir, r"Environment\translator-project.json")


def BatchTranslate(data : pd.Series) -> pd.Series:
	translate_client = translate.Client()
	s_Translated = []
	
	for i in range(len(data)):
	#for i in range(10): # Testing purpose
		translation = translate_client.translate(str(data[i]), target_language='en', source_language='pt-br')
		s_Translated.append(translation['translatedText'])

	s_Translated = pd.Series(s_Translated)

	return s_Translated

