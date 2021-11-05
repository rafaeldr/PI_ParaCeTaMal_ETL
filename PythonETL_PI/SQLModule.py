import pandas as pd
import re

class SQLScripting:

    df : pd.DataFrame

    def __init__(self, df, table_name):
        self.df = df
        self.table_name = table_name
        self.gen_CreateTableSQL()

    def gen_CreateTableSQL(self):
        table_name = self.table_name
        df = self.df

        insert = """
        CREATE TABLE '{dest_table}' (
            """.format(dest_table=table_name)
        
        columns_string = str(list(df.columns))[1:-1] # brackets
        columns_string = re.sub(r' ', '\n        ', columns_string)
        columns_string = re.sub(r'\'', '', columns_string)

        values_string = ''

        for row in df.itertuples(index=False,name=None):
            values_string += re.sub(r'nan', 'null', str(row))
            values_string += ',\n'

        return insert + columns_string + ')\n     VALUES\n' + values_string[:-2] + ';'



    def get_insert_query_from_df(df, dest_table):

        insert = """
        INSERT INTO `{dest_table}` (
            """.format(dest_table=dest_table)

        columns_string = str(list(df.columns))[1:-1]
        columns_string = re.sub(r' ', '\n        ', columns_string)
        columns_string = re.sub(r'\'', '', columns_string)

        values_string = ''

        for row in df.itertuples(index=False,name=None):
            values_string += re.sub(r'nan', 'null', str(row))
            values_string += ',\n'

        return insert + columns_string + ')\n     VALUES\n' + values_string[:-2] + ';'