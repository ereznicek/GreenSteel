# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 13:29:30 2022

@author: mkoleva
"""

# Specify file path to PyFAST
import sys
import os
import glob
sys.path.insert(1,'../PyFAST/')
import pandas as pd
sys.path.append('../PyFAST/')
import run_profast_for_hydrogen_SMR
sys.path.append('')
import warnings
warnings.filterwarnings("ignore")
#import examples.hopp_tools_steel
import hopp_tools_steel
#from examples import hopp_tools
#import examples.hopp_tools

parent_path = os.path.abspath('')
dir1 = os.getcwd()
dirin_el_prices = 'H2_Analysis/'
el_prices_files = glob.glob(os.path.join(dir1 + dirin_el_prices, 'annual_average_retail_prices.csv'))
renewable_cost_path = ('H2_Analysis/green_steel_site_renewable_costs_ATB_aug2024.xlsx')
#fin_sum_dir = parent_path + '/Results_SMR'
#price_breakdown_dir = parent_path + '/H2_Analysis/Phase1B/SMR_ProFAST_price/'

fin_sum_dir = os.path.join(parent_path,"Results_SMR", "Fin_sum")
price_breakdown_dir = os.path.join(parent_path,"Results_SMR", "ProFAST")

lcoh_check_all = []
lcoh = []
years_all = []
sites_all = []
policy_all = []
NG_price_all = []
scenario = dict()
scenario['Wind PTC'] = 0.0
SMR_LCOH_dic = {'Year':[], 'Location':[], 'Policy': [], 'NG price case': [], 'LCOH':[], 'LCOA':[], 'LCOS':[]}

atb_years = [
            2022,
            2025,
            2030,
            2035
            ]
    
site_selection = [
                'Site 1',
                'Site 2',
                'Site 3',
                'Site 4',
                'Site 5',
                ] 

policy_cases = [
                'no policy',
                'base',
                'max'
] 
#['no policy', 'base', 'max']

''' SMR doesn't get any of the policy options below:
'''
#policy_option = {
    #'no policy': {'Wind ITC': 0, 'Wind PTC': 0, "H2 PTC": 0, 'Storage ITC': 0},
    #'base': {'Wind ITC': 0, 'Wind PTC': 0.006, "H2 PTC": 0.6, 'Storage ITC': 6},
    #'max': {'Wind ITC': 0, 'Wind PTC': 0.029, "H2 PTC": 3.0, 'Storage ITC': 50},
    # 'max on grid hybrid': {'Wind ITC': 0, 'Wind PTC': 0.006, "H2 PTC": 0.60, 'Storage ITC': 6},
    # 'max on grid hybrid': {'Wind ITC': 0, 'Wind PTC': 0.029, "H2 PTC": 0.60, 'Storage ITC': 50},
    # 'option 3': {'Wind ITC': 6, 'Wind PTC': 0, "H2 PTC": 0.6},
    # 'option 4': {'Wind ITC': 30, 'Wind PTC': 0, "H2 PTC": 3},
    # 'option 5': {'Wind ITC': 50, 'Wind PTC': 0, "H2 PTC": 3},
#}

NG_price_cases = [
                  'default',
                  'min',
                  'max',
                  ]
CCS_options = ['wCCS',
               'woCCS'
             ]

o2_heat_integration = 0 # should always be set to zero in this scenario

# Site specific turbine information
xl = pd.ExcelFile(renewable_cost_path)

scenario_df = xl.parse()
scenario_df.set_index(["Parameter"], inplace = True)

for atb_year in atb_years:
    for site_location in site_selection:
        for policy_case in policy_cases:
            for CCS_option in CCS_options:
                for NG_price_case in NG_price_cases:
                    if NG_price_case == 'default':
                        grid_price_filename = 'annual_average_retail_prices_adder.csv'
                    elif NG_price_case == 'min':
                        grid_price_filename = 'annual_average_ws_prices.csv'
                    elif NG_price_case == 'max':
                        grid_price_filename = 'annual_average_retail_prices_adder.csv'
                    site_df = scenario_df[site_location]                
                    site_name = site_df['State']                
                    hydrogen_annual_production, hydrogen_storage_duration_hr, lcoh, lcoh_breakdown,profast_h2_price_breakdown,lcoe, plant_life,\
                    price_breakdown_storage,price_breakdown_compression,\
                    price_breakdown_SMR_plant,\
                    CO2_TnS_unit_cost,\
                    price_breakdown_SMR_FOM, price_breakdown_SMR_VOM,\
                    price_breakdown_SMR_NG, price_breakdown_SMR_E,\
                    price_breakdown_taxes,\
                    price_breakdown_water_charges,\
                    remaining_financial,\
                    h2_production_capex = \
                    run_profast_for_hydrogen_SMR.run_profast_for_hydrogen_SMR(atb_year,site_name,site_location,policy_case,NG_price_case,CCS_option,grid_price_filename)
    
                    lime_unit_cost = site_df['Lime ($/metric tonne)'] + site_df['Lime Transport ($/metric tonne)']
                    carbon_unit_cost = site_df['Carbon ($/metric tonne)'] + site_df['Carbon Transport ($/metric tonne)']
                    iron_ore_pellets_unit_cost = site_df['Iron Ore Pellets ($/metric tonne)'] + site_df['Iron Ore Pellets Transport ($/metric tonne)']
                    steel_economics_from_pyfast, steel_economics_summary, profast_steel_price_breakdown,steel_breakeven_price, steel_annual_production_mtpy,steel_price_breakdown,steel_plant_capex = \
                                                                                    hopp_tools_steel.steel_LCOS_SMR(lcoh,hydrogen_annual_production,
                                                                                                                            lime_unit_cost,
                                                                                                                            carbon_unit_cost,
                                                                                                                            iron_ore_pellets_unit_cost,
                                                                                                                            lcoe, scenario, NG_price_case, o2_heat_integration,atb_year,site_name,grid_price_filename)
                    
                    cooling_water_cost = 0.00013817 # 2020$/Gal
                    iron_based_catalyst_cost = 28.2805 # 2020$/kg
                    #oxygen_cost = 0.03476   # 2020$/kg 
                    oxygen_cost = 0
                    ammonia_economics_from_pyfast, ammonia_economics_summary, profast_ammonia_price_breakdown,ammonia_breakeven_price, ammonia_annual_production_kgpy,ammonia_price_breakdown,ammonia_plant_capex = \
                                                                                    hopp_tools_steel.levelized_cost_of_ammonia_SMR(lcoh,hydrogen_annual_production,
                                                                                                                            cooling_water_cost,
                                                                                                                            iron_based_catalyst_cost,
                                                                                                                            oxygen_cost, 
                                                                                                                            lcoe, scenario,atb_year,site_name,grid_price_filename)

                    lcoe_first_year = lcoe[atb_year+5]
                    atb_year, lcoh = hopp_tools_steel.write_outputs_ProFAST_SMR(fin_sum_dir,price_breakdown_dir,atb_year,
                                site_name,
                                lcoe_first_year,
                                lcoh,
                                NG_price_case,
                                hydrogen_storage_duration_hr,
                                hydrogen_annual_production,
                                price_breakdown_storage,price_breakdown_compression,
                                price_breakdown_SMR_plant,
                                CO2_TnS_unit_cost,
                                price_breakdown_SMR_FOM, price_breakdown_SMR_VOM,
                                price_breakdown_SMR_NG, price_breakdown_SMR_E,
                                price_breakdown_taxes,
                                price_breakdown_water_charges,
                                remaining_financial,
                                steel_annual_production_mtpy,
                                steel_breakeven_price,
                                steel_price_breakdown,
                                ammonia_annual_production_kgpy,
                                ammonia_breakeven_price,
                                ammonia_price_breakdown,policy_case,CCS_option,o2_heat_integration,
                                h2_production_capex,
                                steel_plant_capex,
                                ammonia_plant_capex,
                                profast_h2_price_breakdown,
                                profast_steel_price_breakdown,
                                profast_ammonia_price_breakdown) 

