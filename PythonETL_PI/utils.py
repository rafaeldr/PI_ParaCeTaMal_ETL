import pandas as pd
import numpy as np
import time

class TimeTracker:

	df_subjects = pd.DataFrame(columns=['subject','start','end'])
	exp_csv_ComputingTime = r"..\Exported\exp_csv_ComputingTime.csv"

	def __init__(self, export_csv_path):
		self.exp_csv_ComputingTime = export_csv_path
		pass

	def note(self, noteSubject : str, strStartEnd : str):
	
		if strStartEnd == 'start':

			if len(self.df_subjects) > 0:
				if noteSubject in self.df_subjects['subject']:
					print('Unexpected error: Subject of note time already started, multiple calls for same purpose.')
					exit(1)

			self.df_subjects = self.df_subjects.append({'subject': noteSubject,
				 'start': time.time(),
				 'end': -1
				}, ignore_index=True)

		elif strStartEnd == 'end':
		
			if len(self.df_subjects) == 0:
				print('Unexpected error: Time call an end while empty.')
				exit(1)
		
			if not any(self.df_subjects['subject']==noteSubject):
				print('Unexpected error: Subject of note time not yet started, but called for an end.')
				exit(1)
			
			index = self.df_subjects.index[self.df_subjects['subject']==noteSubject][0]
			self.df_subjects.iloc[index, 2] = time.time()
		
		else:
			print('Unexpected error: Unknown command passed to function utils.noteTime()')
			exit(1)

		return

	def export(self):

		self.df_subjects.to_csv(self.exp_csv_ComputingTime, encoding="utf-8", index = False)