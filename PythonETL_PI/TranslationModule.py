import pandas as pd
import numpy as np
import collections

import six
from google.cloud import translate_v2 as translate

import os
parentDir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(parentDir, r"Environment\translator-project.json")

# Translator Test
translate_client = translate.Client()
result = translate_client.translate('lepirudina', target_language='en', source_language='pt-br')