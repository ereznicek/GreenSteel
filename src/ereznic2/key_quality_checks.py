import os
import sys
sys.path.append('')
from dotenv import load_dotenv
import pandas as pd

import numpy as np
import numpy_financial as npf
import matplotlib.pyplot as plt
import warnings
from pathlib import Path
import sqlite3
import openpyxl


parent_path = os.path.abspath('')

# Initialization and Global Settings
#Specify directory name
main_directory = 'Results_main/Fin_sum'
#main_directory = 'Results_sensitivity/Fin_sum'

retail_string = 'retail-flat'

# Read in the summary data from the database
conn = sqlite3.connect(main_directory+'/Default_summary.db')
financial_summary  = pd.read_sql_query("SELECT * From Summary",conn)

conn.commit()
conn.close()

# Order matrix by location
financial_summary.loc[financial_summary['Site']=='IN','Order']= 0
financial_summary.loc[financial_summary['Site']=='TX','Order']= 1
financial_summary.loc[financial_summary['Site']=='IA','Order']= 2
financial_summary.loc[financial_summary['Site']=='MS','Order']= 3
financial_summary.loc[financial_summary['Site']=='MN','Order']= 4

# Narrow down to retail price of interest
if retail_string == 'retail-flat':
    financial_summary = financial_summary.loc[(financial_summary['Grid case']!='grid-only-wholesale') & (financial_summary['Grid case']!='hybrid-grid-wholesale') & (financial_summary['Grid case'] != 'grid-only-retail-flat')]
elif retail_string == 'wholesale':
    financial_summary = financial_summary.loc[(financial_summary['Grid Case']!='grid-only-retail-flat') & (financial_summary['Grid Case']!='hybrid-grid-retail-flat')& (financial_summary['Grid case'] != 'grid-only-wholesale')]


# Policy option
policy_options = [
                'no-policy',
                'base',
                'max'
                ]

# Electrolysis case 
electrolysis_case = 'Centralized'

electrolysis_cost_case = 'mid'

locations = [
            'IN',
            'TX',
            'IA',
            'MS',
            'MN'
             ]


years = [
    '2022',
    '2025',
    '2030',
    '2035'
    ]

retail_string = 'retail-flat'

grid_cases = [
             'off-grid',
             #'hybrid-grid'+'-' + retail_string,
             #'grid-only' + '-' + retail_string
             ]

financial_summary = financial_summary.loc[(financial_summary['Site'].isin(locations)) & (financial_summary['Year'].isin(years)) & (financial_summary['Grid case'].isin(grid_cases))]

key_checks_df = financial_summary[['Site','Year','Policy Option','Grid case','Excess VRE capacity (%)','Steel annual capacity margin (%)']]


[]