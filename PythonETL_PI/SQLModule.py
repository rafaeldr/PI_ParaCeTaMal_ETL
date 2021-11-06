import pandas as pd
import re

class SQLScripting:

    df : pd.DataFrame
    types_list = []
    column_names = [] # Empty list means all DataFrame columns
    pk_list = [] # Empty list means no PK
    fk_list = [] # Empty list means no FK
    fk_ext_table = [] # External table referenced by FK; "ordered" | Validity of correspondence will not be checked
    fk_ext_column = [] # External columns referenced by FK; "ordered" | Validity of correspondence will not be checked
    

    # Map pd.dtype to MySQL Type
    dict_type = {'INT32': 'INT',
                 'INT64': 'INT',
                 'FLOAT32': 'DOUBLE',
                 'FLOAT64': 'DOUBLE',
                 'STRING': 'VARCHAR(250)',
                 'BOOL': 'BOOLEAN'}


    def __init__(self, df, table_name, column_names = [], types_list = [], pk_list = [], fk_list = [], fk_ext_table = [], fk_ext_column = []):
        self.df = df
        self.table_name = table_name
        self.checkColumnNames(column_names, pk_list, fk_list, fk_ext_table, fk_ext_column)
        self.types_list = types_list if (types_list) else self.inferDataTypes()
        self.createSQL = self.gen_CreateTableSQL()


    def gen_CreateTableSQL(self):

        create_string = "CREATE TABLE '{dest_table}' (\n".format(dest_table=self.table_name)
        indent = ' ' * 4

        columns_string = ""
        for i in range(len(self.df.columns)):
            col_name = str(self.df.columns[i])
            col_type = self.types_list[i]
            columns_string += indent + col_name + ' ' + col_type + ',\n'

        pk_string = ""
        if self.pk_list:
            pk_string += indent + 'PRIMARY KEY ('
            for pk in self.pk_list:
                pk_string += pk + ', '
            pk_string = pk_string[:-2] + '),\n'

        fk_string = ""
        if self.fk_list:
            for i in range(len(self.fk_list)):
                fk_string += indent + 'FOREIGN KEY (' + self.fk_list[i] 
                fk_string += ') REFERENCES ' + self.fk_ext_table[i] + '(' + self.fk_ext_column[i] + '),\n'

        return_string = create_string + columns_string + pk_string + fk_string
        return_string = return_string[:-2] + '\n);'
                
        return return_string


    def gen_InsertSQL(df, dest_table):

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


    # Infer datatypes when not provided user call
    def inferDataTypes(self):

        types_list = []

        # Try to auto infer data types (when not provided by DataFrame inner structure)
        if any(self.df.dtypes=='object'):
            self.df = self.df.convert_dtypes()
            if any(self.df.dtypes=='object'):
                print('Unexpected error: Failed to automatically infer DataFrame data types, consider providing it manually!')
                exit(1)

        # Populate Types List from Class Dictionary
        for dtype in self.df.dtypes:
            types_list.append(self.dict_type[str(dtype).upper()])

        return types_list


    # They must exist + Not provided must be removed + Keep provided order
    def checkColumnNames(self, column_names = [], pk_list = [], fk_list = [], fk_ext_table = [], fk_ext_column = []):

        # Check existance
        if column_names:
            if not set(column_names).issubset(self.df.columns):
                print('Unexpected error: Provided column does not exist in the provided DataFrame!')
                exit(1)
            # Force order provided by the list
            self.df = self.df[column_names]
        else:
            pass # keep default class behavior
        
        # Check PK
        if pk_list:
            if not set(pk_list).issubset(self.df.columns):
                print('Unexpected error: Provided Primary Keys does not exist in the provided DataFrame!')
                exit(1)
        
        # Check FK
        if fk_list:
            if not set(fk_list).issubset(self.df.columns):
                print('Unexpected error: Provided Foreign Keys does not exist in the provided DataFrame!')
                exit(1)

        # FK Minimum Consistency
        if len(fk_list) != len(fk_ext_table) or len(fk_ext_table) != len(fk_ext_column):
            print('Unexpected error: Provided Foreign Keys info does not match! Provide the appropriate/complete info!')
            exit(1)

        self.column_names = column_names
        self.pk_list = pk_list
        self.fk_list = fk_list
        self.fk_ext_table = fk_ext_table
        self.fk_ext_column = fk_ext_column
        return


exp_csv_drugs = r"..\DataSources\exp_csv_drugs.csv"
df_drugs = pd.read_csv(exp_csv_drugs, sep=',')
sqlDrugBank_Name = SQLScripting(df_drugs,'DrugBank_Nome')
#sqlDrugBank_Name = SQLScripting(df_drugs,'DrugBank_Nome', [], [], ['drugbank-id'], ['name'], ['Anvisa_Name'], ['nome'])