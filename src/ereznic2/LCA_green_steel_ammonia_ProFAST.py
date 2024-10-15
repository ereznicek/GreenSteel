# -*- coding: utf-8 -*-
"""
Created on Fri Apr 22 10:44:27 2022

@author: ereznic2
"""

import fnmatch
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import sqlite3

import glob
import csv
import sys
import heapq

import matplotlib.colors as mcolorsg
import matplotlib.ticker as ticker
import matplotlib.axes as axes

# Directory from which to pull outputs from
parent_path = os.path.abspath('')
#Specify directory name
electrolysis_directory = 'Results_main/Fin_sum/'
dirprofiles = 'Results_main/Profiles/' 
dircambium = 'H2_Analysis/Cambium_data/Cambium22_MidCase100by2035_hourly_' 
sensitivity_directory = 'Results_sensitivity/Fin_sum/'
smr_directory = 'Results_SMR/Fin_sum/'
plot_directory = 'Plots'
plot_subdirectory = 'LCA_Plots'

# Specify grid price scenario if interest for down-selection in case multiple grid scenarios
# exist within the output folder
# grid_connection_cases ['off-grid','grid-only','hybrid-grid']
# Grid price scenario ['wholesale','retail-peaks','retail-flat']
# Retail price of interest ['retail-flat','wholesale']
retail_string = 'retail-flat'

solar_size_mw = 0
storage_size_mw = 0

c0 = [0,0,0]

files2load_results={}
files2load_results_title={}
files2load_results_categories={}


for files2load in os.listdir(dirprofiles):
    if fnmatch.fnmatch(files2load, 'Energy_*'):
        c0[0]=c0[0]+1
        files2load_results[c0[0]] = files2load
        int1 = files2load.split("_")
        int1 = int1[1:]
        int1[-1] = int1[-1].replace('.csv', '')
        files2load_results_title[c0[0]] = int1
    files2load_title_header = ['Site','Year','Turbine Size','Electrolysis case','Electrolysis cost case','Policy Option','Grid case','Renewables case','Wind model','Degradation modeled?','Stack optimized?','NPC string','Num pem clusters','Storage string','Storage multiplier']
#==============================================================================
# DATA
#==============================================================================        
# Conversions
g_to_kg_conv  = 0.001  # Conversion from grams to kilograms
kg_to_MT_conv = 0.001 # Converion from kg to metric tonnes
MT_to_kg_conv = 1000 # Conversion from metric tonne to kilogram
kWh_to_MWh_conv = 0.001 # Conversion from kWh to MWh

#------------------------------------------------------------------------------
# Renewable infrastructure embedded emission intensities
#------------------------------------------------------------------------------
system_life        = 30
ely_stack_capex_EI = 0.019 # PEM electrolyzer CAPEX emissions (kg CO2e/kg H2)
wind_capex_EI      = 10    # Electricity generation from wind, nominal value taken (g CO2e/kWh)
#wind_capex_EI_perMW = 34882
solar_pv_capex_EI = 37
battery_EI = 20
# if solar_size_mw != 0:
#     solar_pv_capex_EI = 37     # Electricity generation capacity from solar pv, nominal value taken (g CO2e/kWh)
#     #solar_pv_capex_EI_perMW = 61777
# else:
#     solar_pv_capex_EI = 0   # Electricity generation capacity from solar pv, nominal value taken (g CO2e/kWh)
#     #solar_pv_capex_EI_perMW = 0
# if storage_size_mw != 0:
#     battery_EI = 20             # Electricity generation capacity from battery (g CO2e/kWh)
# else:
#     battery_EI = 0  # Electricity generation capacity from battery (g CO2e/kWh)

# Other grid infrastructure imbedded emission intensities
nuclear_capex_EI = 0.3 # g CO2e/kWh
coal_capex_EI = 0.8  # g CO2e/kWh
gas_capex_EI = 0.42  # g CO2e/kWh
hydro_capex_EI = 7.22 # g CO2e/kWh
bio_capex_EI = 0.81 # g CO2e/kWh
geothermal_capex_EI = 20.71 # g CO2e/kWh

NG_supply_EI = 12.68 # Natural gas extraction and supply to production plants (g CO2e/MJ)
NG_combust_EI = 56.27 # Natural gas consumption emissions (g CO2e/MJ)

smr_El_wCCS_consume = 1.78 # kWh/kg H2
smr_El_woCCS_consume = 0.16 # kWh/kg H2

#------------------------------------------------------------------------------
# Steam methane reforming (SMR) - Incumbent H2 production process
#------------------------------------------------------------------------------

smr_NG_combust = NG_combust_EI # Natural gas combustion (g CO2e/MJ)
smr_NG_consume = 161  # Natural gas consumption for combustion and CO2 balance (MJ/kg H2)
smr_NG_consume_CCS = 171 # Natural gas consumption for combustion and CO2 balance (MJ-LHV/kg-H2) for SMR+CCS
smr_PO_consume = smr_El_woCCS_consume    # Power consumption in SMR plant (kWh/kg H2)
smr_ccs_PO_consume = smr_El_wCCS_consume # Power consumption in SMR CCS plant (kWh/kg H2)
smr_steam_prod = 30.18 # Steam production on SMR site (MJ/kg H2)
smr_HEX_eff    = 0.9  # Heat exchanger efficiency (-)
smr_NG_supply  = NG_supply_EI    # Natural gas extraction and supply to SMR plant assuming 2% CH4 leakage rate (g CO2e/MJ)
ccs_perc_capture = 0.95 # Carbon capture rate (-)


#------------------------------------------------------------------------------
# Autothermal reforming (ATR) with CCS
#------------------------------------------------------------------------------

atr_NG_combust   = 56.2 # Natural gas combustion (g CO2e/MJ)
atr_NG_supply    = NG_supply_EI      # Natural gas extraction and supply to SMR plant assuming 2% CH4 leakage rate (g CO2e/MJ)
atr_PO_consume   = 15.08   # Electricity consumption in the ATR plant (MJ/kg H2)
atr_NG_consume   = 256.7  # Includes natural gas consumption for CO2 balance and the fired heater (assuming it is using natural gas) (MJ/kg H2)
atr_H2O_consume  = 0.012 # metric ton per 1 kg H2
atr_perc_capture = 0.94496 # Carbon capture rate (-)
atr_CO2_reduction = 0.17 # kg CO2 per kg H2

#------------------------------------------------------------------------------
# Hydrogen production via water electrolysis
#------------------------------------------------------------------------------

grid_trans_losses   = 0.05 # Grid losses of 5% are assumed (-)
fuel_to_grid_curr   = 48   # Fuel mix emission intensity for current power grid (g CO2e/kWh)
fuel_to_grid_futu   = 14   # Fuel mix emission intensity for future power grid (g CO2e/kWh)
ely_PO_consume      = 54.61       # kWh/kg H2

#------------------------------------------------------------------------------
# Ammonia
#------------------------------------------------------------------------------

NH3_PO_consume = 0.0609      # Electricity usage (kWh/kg NH3)
NH3_H2_consume = 0.2         # Hydrogen consumption (kg H2/kg NH3)
NH3_boiler_EI  = 0.463       # Boiler combustion of methane (kg CO2e/kg NH3)

#------------------------------------------------------------------------------
# Steel
#------------------------------------------------------------------------------

steel_H2_consume = 0.06596 # metric tonnes of H2 per tonne of steel
steel_NG_consume = 0.71657 # GJ-LHV per tonne of steel
steel_lime_consume = 0.01812 # metric tonne of lime per tonne of steel
steel_iron_ore_consume = 1.629 # metric tonnes of iron ore per metric tonne of steel
steel_PO_consume = 0.5502 # MWh per metric tonne of steel
steel_H2O_consume = 0.8037 # metric tonnes of H2O per tonne of steel
steel_CH4_prod = 39.29	# kg of CO2e emission/metric tonne of annual steel slab production 
steel_CO2_prod = 174.66	# kg of CO2 emission/metric tonne of annual steel slab production 

steel_NG_supply_EI  = NG_supply_EI    # Natural gas extraction and supply to plant assuming 2% CH4 leakage rate (g CO2e/MJ)
steel_lime_EI = 1.28   # kg CO2e/kg lime
steel_iron_ore_EI = 0.46 # kg CO2e/kg iron ore
steel_H2O_EI = 0.0013 # kg CO2e/gal H2O (conservative)
gal_to_ton_conv = 0.001336 # for water conversions

H2_PTC_duration = 10 # years

smr_Scope3_EI = 'NA'
smr_Scope2_EI = 'NA'
smr_Scope1_EI = 'NA'
smr_total_EI  = 'NA'
smr_ccs_Scope3_EI = 'NA'
smr_ccs_Scope2_EI = 'NA'
smr_ccs_Scope1_EI = 'NA'
smr_ccs_total_EI  = 'NA'
NH3_smr_Scope3_EI = 'NA'
NH3_smr_Scope2_EI = 'NA'
NH3_smr_Scope1_EI = 'NA'
NH3_smr_total_EI  = 'NA'
NH3_smr_ccs_Scope3_EI = 'NA'
NH3_smr_ccs_Scope2_EI = 'NA'
NH3_smr_ccs_Scope1_EI = 'NA'
NH3_smr_ccs_total_EI  = 'NA'
steel_smr_Scope3_EI = 'NA'
steel_smr_Scope2_EI = 'NA'
steel_smr_Scope1_EI = 'NA'
steel_smr_total_EI  = 'NA'
steel_smr_ccs_Scope3_EI = 'NA'
steel_smr_ccs_Scope2_EI = 'NA'
steel_smr_ccs_Scope1_EI = 'NA'
steel_smr_ccs_total_EI  = 'NA'
atr_ccs_Scope3_EI = 'NA'
atr_ccs_Scope2_EI = 'NA'
atr_ccs_Scope1_EI = 'NA'
atr_ccs_total_EI  = 'NA'
NH3_atr_ccs_Scope3_EI = 'NA'
NH3_atr_ccs_Scope2_EI = 'NA'
NH3_atr_ccs_Scope1_EI = 'NA'
NH3_atr_ccs_total_EI  = 'NA'
steel_atr_ccs_Scope3_EI = 'NA'
steel_atr_ccs_Scope2_EI = 'NA'
steel_atr_ccs_Scope1_EI = 'NA'
steel_atr_ccs_total_EI  = 'NA'
electrolysis_Scope3_EI = 'NA'
electrolysis_Scope2_EI = 'NA'
electrolysis_Scope1_EI = 'NA'
electrolysis_total_EI  = 'NA'
NH3_electrolysis_Scope3_EI = 'NA'
NH3_electrolysis_Scope2_EI = 'NA'
NH3_electrolysis_Scope1_EI = 'NA'
NH3_electrolysis_total_EI  = 'NA'
steel_electrolysis_Scope3_EI = 'NA'
steel_electrolysis_Scope2_EI = 'NA'
steel_electrolysis_Scope1_EI = 'NA'
steel_electrolysis_total_EI  = 'NA'

#==============================================================================
    
# Loop through all scenarios in output folder
for i0 in range(len(files2load_results)):
    #i0=65
    # Read in applicable Cambium file
    filecase = files2load_results_title[i0+1]
    # Extract year and site location to identify which cambium file to import
    year = int(filecase[1])
    site_name = filecase[0]
    grid_case = filecase[6]
    # The arguments below are just starting points
    
    if year == 2022:
        cambium_year = 2030
    elif year == 2025:
        cambium_year = 2030
    elif year == 2030:
        cambium_year =2035
    elif year == 2035:
        cambium_year = 2040
    
    # Read in the cambium 
    electrolysis_emission_intensity = []
    electrolysis_Scope3_emission_intensity = []
    electrolysis_Scope2_emission_intensity = []
    smr_Scope3_emission_intensity = []
    smr_Scope2_emission_intensity = []
    smr_emission_intensity = []
    smr_ccs_Scope3_emission_intensity = []
    smr_ccs_Scope2_emission_intensity = []
    smr_ccs_emission_intensity = []
    atr_ccs_Scope3_emission_intensity = []
    atr_ccs_Scope2_emission_intensity = []
    atr_ccs_emission_intensity = []
    NH3_electrolysis_Scope3_emission_intensity = []
    NH3_electrolysis_Scope2_emission_intensity = []
    NH3_electrolysis_emission_intensity = []
    steel_electrolysis_Scope3_emission_intensity = []
    steel_electrolysis_Scope2_emission_intensity = []
    steel_electrolysis_emission_intensity = []
    NH3_smr_Scope3_emission_intensity = []
    NH3_smr_Scope2_emission_intensity = []
    NH3_smr_emission_intensity = []
    steel_smr_Scope3_emission_intensity = []
    steel_smr_Scope2_emission_intensity = []
    steel_smr_emission_intensity = []
    NH3_smr_ccs_Scope3_emission_intensity = []
    NH3_smr_ccs_Scope2_emission_intensity = []
    NH3_smr_ccs_emission_intensity = []
    steel_smr_ccs_Scope3_emission_intensity = []
    steel_smr_ccs_Scope2_emission_intensity = []
    steel_smr_ccs_emission_intensity = []    
    NH3_atr_ccs_Scope3_emission_intensity = []
    NH3_atr_ccs_Scope2_emission_intensity = []
    NH3_atr_ccs_emission_intensity = []
    steel_atr_ccs_Scope3_emission_intensity = []
    steel_atr_ccs_Scope2_emission_intensity = []
    steel_atr_ccs_emission_intensity = []

    # Read in financial summary to determine if there is any solar or batteries
    if grid_case != 'grid-only-retail-flat':
        hopp_finsum_filepath =electrolysis_directory+'Fin_sum'
        for j in range(len(filecase)):
            hopp_finsum_filepath = hopp_finsum_filepath + '_' +filecase[j]
        hopp_finsum_filepath = hopp_finsum_filepath + '.csv'
        hopp_finsum = pd.read_csv(hopp_finsum_filepath,index_col=None,header=0).set_index(['Unnamed: 0']).T
        hopp_finsum = hopp_finsum.drop(['Fraction of electricity from renewables (-)'],axis=1)
        hopp_finsum = hopp_finsum.astype(float)

        

        solar_size_mw = hopp_finsum['Solar capacity (MW)'].values.tolist()[0]
        storage_size_mw = hopp_finsum['Battery storage capacity (MW)'].values.tolist()[0]

    #     if solar_size_mw != 0:
    #         solar_pv_capex_EI = 37     # Electricity generation capacity from solar pv, nominal value taken (g CO2e/kWh)
    #         #solar_pv_capex_EI_perMW = 61777
    #     else:
    #         solar_pv_capex_EI = 0   # Electricity generation capacity from solar pv, nominal value taken (g CO2e/kWh)
    #         #solar_pv_capex_EI_perMW = 0

    #     if storage_size_mw != 0:
    #         battery_EI = 20             # Electricity generation capacity from battery (g CO2e/kWh)
    #     else:
    #         battery_EI = 0  # Electricity generation capacity from battery (g CO2e/kWh)
    # #else:
    #    solar_pv_capex_EI=0
    #    battery_EI=0    

    # Read in HOPP data
    hopp_profiles_filepath =dirprofiles + 'Energy'
    for j in range(len(filecase)):
        hopp_profiles_filepath = hopp_profiles_filepath + '_' + filecase[j]
    
    hopp_profiles_filepath = hopp_profiles_filepath + '.csv'
    hopp_profiles_data = pd.read_csv(hopp_profiles_filepath,index_col=None,header=0,usecols=['Energy to electrolyzer (kWh)','Energy from grid (kWh)','Energy from renewables (kWh)','Hydrogen Hourly production (kg)'])
    hopp_profiles_data=hopp_profiles_data.reset_index().rename(columns={'index':'Interval'})
    hopp_profiles_data['Interval'] = hopp_profiles_data['Interval']+1
    hopp_profiles_data = hopp_profiles_data.set_index('Interval')

    # Read in cambium data and combine with hopp data
    years = list(range(cambium_year,2055,5))
    for year in years:
        cambiumdata_filepath = dircambium + site_name + '_'+str(year) + '.csv'
        cambium_data = pd.read_csv(cambiumdata_filepath,index_col = None,header = 5,usecols = ['lrmer_co2_c','lrmer_ch4_c','lrmer_n2o_c','lrmer_co2_p','lrmer_ch4_p','lrmer_n2o_p','lrmer_co2e_c','lrmer_co2e_p','lrmer_co2e',\
                                                                                               'generation','nuclear_MWh','coal_MWh','coal-ccs_MWh','o-g-s_MWh','gas-cc_MWh','gas-cc-ccs_MWh','gas-ct_MWh','hydro_MWh','geothermal_MWh',\
                                                                                                'biomass_MWh','beccs_MWh','wind-ons_MWh','wind-ofs_MWh','csp_MWh','upv_MWh','distpv_MWh','phs_MWh','battery_MWh','canada_MWh'])

        cambium_data = cambium_data.reset_index().rename(columns = {'index':'Interval','lrmer_co2_c':'LRMER CO2 combustion (kg-CO2/MWh)','lrmer_ch4_c':'LRMER CH4 combustion (g-CH4/MWh)','lrmer_n2o_c':'LRMER N2O combustion (g-N2O/MWh)',\
                                                    'lrmer_co2_p':'LRMER CO2 production (kg-CO2/MWh)','lrmer_ch4_p':'LRMER CH4 production (g-CH4/MWh)','lrmer_n2o_p':'LRMER N2O production (g-N2O/MWh)','lrmer_co2e_c':'LRMER CO2 equiv. combustion (kg-CO2e/MWh)',\
                                                    'lrmer_co2e_p':'LRMER CO2 equiv. production (kg-CO2e/MWh)','lrmer_co2e':'LRMER CO2 equiv. total (kg-CO2e/MWh)'})

        cambium_data['Interval']=cambium_data['Interval']+1
        cambium_data = cambium_data.set_index('Interval')

        #hopp_profiles_filepath =dirprofiles+files2load_results[i0+1] 
        #hopp_profiles_data = pd.read_csv(hopp_profiles_filepath,index_col=None,header=0,usecols=['Energy to electrolyzer (kWh)','Energy from grid (kWh)','Energy from renewables (kWh)','Hydrogen Hourly production (kg)'])
        # hopp_profiles_data=hopp_profiles_data.reset_index().rename(columns={'index':'Interval'})
        # hopp_profiles_data['Interval'] = hopp_profiles_data['Interval']+1
        # hopp_profiles_data = hopp_profiles_data.set_index('Interval')
        combined_data = pd.concat([hopp_profiles_data,cambium_data],axis=1)

        # Calculate hourly grid emissions factors of interest. If we want to use different GWPs, we can do that here. The Grid Import is an hourly data i.e., in MWh
        combined_data['Total grid emissions (kg-CO2e)'] = combined_data['Energy from grid (kWh)'] * combined_data['LRMER CO2 equiv. total (kg-CO2e/MWh)'] / 1000
        combined_data['Scope 2 (combustion) grid emissions (kg-CO2e)'] = combined_data['Energy from grid (kWh)'] * combined_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'] / 1000
        combined_data['Scope 3 (production) grid emissions (kg-CO2e)'] = combined_data['Energy from grid (kWh)'] * combined_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'] / 1000
        # Sum total emissions
        #scope2_grid_emissions_sum = combined_data['Scope 2 (combustion) grid emissions (kg-CO2e)'].sum()*kg_to_MT_conv
        #scope3_grid_emissions_sum = combined_data['Scope 3 (production) grid emissions (kg-CO2e)'].sum()*kg_to_MT_conv
        #scope3_ren_sum            = energy_from_renewables_df['Energy from renewables (kWh)'].sum()/1000 # MWh
        #scope3_ren_sum            = combined_data['Energy from renewables (kWh)'].sum()/1000 # MWh
        #h2prod_sum = np.sum(hydrogen_production_while_running)*system_life*kg_to_MT_conv
    #    h2prod_grid_frac = cambium_data['Grid Import (MW)'].sum() / cambium_data['Electrolyzer Power (MW)'].sum()
        h2prod_annual_sum = combined_data['Hydrogen Hourly production (kg)'].sum()
        h2prod_life_sum = combined_data['Hydrogen Hourly production (kg)'].sum()*system_life
        # Sum total emissions
        total_grid_emissions_annual_sum = combined_data['Total grid emissions (kg-CO2e)'].sum()
        scope2_grid_emissions_annual_sum = combined_data['Scope 2 (combustion) grid emissions (kg-CO2e)'].sum()
        scope3_grid_emissions_annual_sum = combined_data['Scope 3 (production) grid emissions (kg-CO2e)'].sum()
        ren_annual_sum_MWh= combined_data['Energy from renewables (kWh)'].sum()/1000 # MWh
        grid_annual_sum_MWh = combined_data['Energy from grid (kWh)'].sum()/1000 # MWh
        grid_emission_intensity_annual_average = combined_data['LRMER CO2 equiv. total (kg-CO2e/MWh)'].mean()

        if grid_case != 'grid-only-retail-flat':
            frac_ren_wind = hopp_finsum['Wind annual energy (MWh)'].values.tolist()[0]/ren_annual_sum_MWh
            frac_ren_solar = hopp_finsum['Solar annual energy (MWh)'].values.tolist()[0]/ren_annual_sum_MWh
        
        # Calculate annual percentages of solar, wind, and fossil
        generation_annual_total_MWh = cambium_data['generation'].sum()
        generation_annual_nuclear_fraction = cambium_data['nuclear_MWh'].sum()/generation_annual_total_MWh
        generation_annual_coal_oil_fraction = (cambium_data['coal_MWh'].sum() + cambium_data['coal-ccs_MWh'].sum() + cambium_data['o-g-s_MWh'].sum())/generation_annual_total_MWh
        generation_annual_gas_fraction = (cambium_data['gas-cc_MWh'].sum() + cambium_data['gas-cc-ccs_MWh'].sum() + cambium_data['gas-ct_MWh'].sum())/generation_annual_total_MWh
        generation_annual_bio_fraction = (cambium_data['biomass_MWh'].sum() + cambium_data['beccs_MWh'].sum())/generation_annual_total_MWh
        generation_annual_geothermal_fraction = cambium_data['geothermal_MWh'].sum()/generation_annual_total_MWh
        generation_annual_hydro_fraction = (cambium_data['hydro_MWh'].sum() + cambium_data['phs_MWh'].sum())/generation_annual_total_MWh
        generation_annual_wind_fraction = (cambium_data['wind-ons_MWh'].sum() + cambium_data['wind-ofs_MWh'].sum())/generation_annual_total_MWh
        generation_annual_solar_fraction = (cambium_data['upv_MWh'].sum() + cambium_data['distpv_MWh'].sum() + cambium_data['csp_MWh'].sum())/generation_annual_total_MWh
        generation_annual_battery_fraction = (cambium_data['battery_MWh'].sum())/generation_annual_total_MWh

        grid_generation_fraction = {'Nuclear':generation_annual_nuclear_fraction,'Coal & Oil':generation_annual_coal_oil_fraction,'Gas':generation_annual_gas_fraction,'Bio':generation_annual_bio_fraction,'Geothermal':generation_annual_geothermal_fraction,\
                                    'Hydro':generation_annual_hydro_fraction,'Wind':generation_annual_wind_fraction,'Solar':generation_annual_solar_fraction,'Battery':generation_annual_battery_fraction}

        grid_imbedded_EI = generation_annual_nuclear_fraction*nuclear_capex_EI + generation_annual_coal_oil_fraction*coal_capex_EI + generation_annual_gas_fraction*gas_capex_EI + generation_annual_bio_fraction*bio_capex_EI\
                         + generation_annual_geothermal_fraction*geothermal_capex_EI + generation_annual_hydro_fraction*hydro_capex_EI+generation_annual_wind_fraction*wind_capex_EI + generation_annual_solar_fraction*solar_pv_capex_EI\
                         + generation_annual_battery_fraction*battery_EI

        if 'hybrid-grid' in grid_case:
            # Calculate grid-connected electrolysis emissions/ future cases should reflect targeted electrolyzer electricity usage
            electrolysis_Scope3_EI = scope3_grid_emissions_annual_sum/h2prod_annual_sum + (wind_capex_EI*hopp_finsum['Wind annual energy (MWh)'].values.tolist()[0] + solar_pv_capex_EI*hopp_finsum['Solar annual energy (MWh)'].values.tolist()[0]+ grid_imbedded_EI*grid_annual_sum_MWh)/h2prod_annual_sum\
                                   +ely_stack_capex_EI # kg CO2e/kg H2
            electrolysis_Scope2_EI = scope2_grid_emissions_annual_sum/h2prod_annual_sum 
            electrolysis_Scope1_EI = 0
            electrolysis_total_EI  = electrolysis_Scope1_EI + electrolysis_Scope2_EI + electrolysis_Scope3_EI 
            electrolysis_total_EI_policy_grid = electrolysis_total_EI
            electrolysis_total_EI_policy_offgrid = 0 
            # Calculate ammonia emissions via hybrid grid electrolysis
            NH3_electrolysis_Scope3_EI = NH3_H2_consume * electrolysis_total_EI + NH3_PO_consume * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + NH3_PO_consume * grid_imbedded_EI * g_to_kg_conv
            NH3_electrolysis_Scope2_EI = NH3_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv
            NH3_electrolysis_Scope1_EI = NH3_boiler_EI
            NH3_electrolysis_total_EI  = NH3_electrolysis_Scope1_EI + NH3_electrolysis_Scope2_EI + NH3_electrolysis_Scope3_EI
            # Calculate steel emissions via hybrid grid electrolysis
            steel_electrolysis_Scope3_EI = (steel_H2_consume * electrolysis_total_EI * MT_to_kg_conv + steel_lime_EI * steel_lime_consume * MT_to_kg_conv + steel_iron_ore_EI  * steel_iron_ore_consume  * MT_to_kg_conv + steel_NG_supply_EI * steel_NG_consume  + cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * steel_PO_consume + steel_H2O_EI * steel_H2O_consume * gal_to_ton_conv)  # kg CO2e/metric tonne steel
            steel_electrolysis_Scope2_EI = steel_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean()  
            steel_electrolysis_Scope1_EI = steel_CH4_prod + steel_CO2_prod
            steel_electrolysis_total_EI  = steel_electrolysis_Scope1_EI + steel_electrolysis_Scope2_EI + steel_electrolysis_Scope3_EI
        if 'grid-only' in grid_case:
            # Calculate SMR emissions. SMR and SMR + CCS are always grid-connected
            smr_Scope3_EI = smr_NG_supply * smr_NG_consume * g_to_kg_conv + smr_PO_consume * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + smr_PO_consume * grid_imbedded_EI * g_to_kg_conv # kg CO2e/kg H2
            smr_Scope2_EI = smr_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv # kg CO2e/kg H2
            smr_Scope1_EI = smr_NG_combust * (smr_NG_consume - smr_steam_prod/smr_HEX_eff) * g_to_kg_conv # kg CO2e/kg H2
            smr_total_EI  = smr_Scope1_EI + smr_Scope2_EI + smr_Scope3_EI
            electrolysis_total_EI_policy_grid = electrolysis_total_EI
            electrolysis_total_EI_policy_offgrid = 0 
            
            # Calculate ammonia emissions via SMR process
            NH3_smr_Scope3_EI = NH3_H2_consume * smr_total_EI + NH3_PO_consume * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + NH3_PO_consume * grid_imbedded_EI * g_to_kg_conv
            NH3_smr_Scope2_EI = NH3_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv
            NH3_smr_Scope1_EI = NH3_boiler_EI
            NH3_smr_total_EI = NH3_smr_Scope1_EI + NH3_smr_Scope2_EI + NH3_smr_Scope3_EI   
            
            # Calculate steel emissions via SMR process
            steel_smr_Scope3_EI = (smr_total_EI * steel_H2_consume * MT_to_kg_conv + steel_lime_EI * steel_lime_consume * MT_to_kg_conv + steel_iron_ore_EI  * steel_iron_ore_consume  * MT_to_kg_conv + steel_NG_supply_EI * steel_NG_consume  + cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * steel_PO_consume + steel_H2O_EI * steel_H2O_consume * gal_to_ton_conv) + steel_PO_consume  * grid_imbedded_EI * g_to_kg_conv # kg CO2e/metric tonne steel
            steel_smr_Scope2_EI = cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * steel_PO_consume 
            steel_smr_Scope1_EI = steel_CH4_prod + steel_CO2_prod
            steel_smr_total_EI  = steel_smr_Scope1_EI + steel_smr_Scope2_EI + steel_smr_Scope3_EI
            
            # Calculate SMR + CCS emissions
            smr_ccs_Scope3_EI = smr_NG_supply * smr_NG_consume_CCS * g_to_kg_conv + smr_ccs_PO_consume * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + smr_ccs_PO_consume * grid_imbedded_EI * g_to_kg_conv # kg CO2e/kg H2
            smr_ccs_Scope2_EI = smr_ccs_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv # kg CO2e/kg H2
            smr_ccs_Scope1_EI = (1-ccs_perc_capture)* smr_NG_combust * smr_NG_consume_CCS * g_to_kg_conv # kg CO2e/kg H2
            smr_ccs_total_EI  = smr_ccs_Scope1_EI + smr_ccs_Scope2_EI + smr_ccs_Scope3_EI    
            
            # Calculate ammonia emissions via SMR with CCS process
            NH3_smr_ccs_Scope3_EI = NH3_H2_consume * smr_ccs_total_EI + NH3_PO_consume * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + NH3_PO_consume * grid_imbedded_EI * g_to_kg_conv
            NH3_smr_ccs_Scope2_EI = NH3_smr_Scope2_EI
            NH3_smr_ccs_Scope1_EI = NH3_smr_Scope1_EI
            NH3_smr_ccs_total_EI = NH3_smr_ccs_Scope1_EI + NH3_smr_ccs_Scope2_EI + NH3_smr_ccs_Scope3_EI   
            
            # Calculate steel emissions via SMR with CCS process
            steel_smr_ccs_Scope3_EI = (smr_ccs_total_EI * steel_H2_consume * MT_to_kg_conv + steel_lime_EI * steel_lime_consume * MT_to_kg_conv + steel_iron_ore_EI  * steel_iron_ore_consume  * MT_to_kg_conv + steel_NG_supply_EI * steel_NG_consume  + cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * steel_PO_consume + steel_H2O_EI * steel_H2O_consume * gal_to_ton_conv) + steel_PO_consume  * grid_imbedded_EI * g_to_kg_conv # kg CO2e/metric tonne steel
            steel_smr_ccs_Scope2_EI = steel_smr_Scope2_EI 
            steel_smr_ccs_Scope1_EI = steel_smr_Scope1_EI 
            steel_smr_ccs_total_EI  = steel_smr_Scope1_EI + steel_smr_Scope2_EI + steel_smr_ccs_Scope3_EI  
            
            # Calculate ATR + CCS emissions
            atr_ccs_Scope3_EI = atr_NG_supply * atr_NG_consume * g_to_kg_conv + atr_PO_consume  * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + atr_PO_consume * grid_imbedded_EI * g_to_kg_conv# kg CO2e/kg H2
            atr_ccs_Scope2_EI = atr_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv # kg CO2e/kg H2
            atr_ccs_Scope1_EI = (1-atr_perc_capture)* atr_NG_combust * atr_NG_consume * g_to_kg_conv # kg CO2e/kg H2
            atr_ccs_total_EI  = atr_ccs_Scope1_EI + atr_ccs_Scope2_EI + atr_ccs_Scope3_EI - atr_CO2_reduction
            
            # Calculate ammonia emissions via ATR with CCS process
            NH3_atr_ccs_Scope3_EI = NH3_H2_consume * atr_ccs_total_EI + NH3_PO_consume * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + NH3_PO_consume * grid_imbedded_EI * g_to_kg_conv
            NH3_atr_ccs_Scope2_EI = NH3_smr_Scope2_EI
            NH3_atr_ccs_Scope1_EI = NH3_smr_Scope1_EI
            NH3_atr_ccs_total_EI = NH3_atr_ccs_Scope1_EI + NH3_atr_ccs_Scope2_EI + NH3_atr_ccs_Scope3_EI   
            
            # Calculate steel emissions via ATR with CCS process

            steel_atr_ccs_Scope3_EI = (atr_ccs_total_EI * steel_H2_consume * MT_to_kg_conv + steel_lime_EI * steel_lime_consume * MT_to_kg_conv + steel_iron_ore_EI  * steel_iron_ore_consume  * MT_to_kg_conv + steel_NG_supply_EI * steel_NG_consume  + cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * steel_PO_consume + steel_H2O_EI * steel_H2O_consume * gal_to_ton_conv)  + steel_PO_consume  * grid_imbedded_EI * g_to_kg_conv # kg CO2e/metric tonne steel
            steel_atr_ccs_Scope2_EI = steel_smr_Scope2_EI 
            steel_atr_ccs_Scope1_EI = steel_smr_Scope1_EI 
            steel_atr_ccs_total_EI  = steel_atr_ccs_Scope1_EI + steel_atr_ccs_Scope2_EI + steel_atr_ccs_Scope3_EI  
                       
            # Calculate grid-connected electrolysis emissions
            electrolysis_Scope3_EI = scope3_grid_emissions_annual_sum/h2prod_annual_sum + (grid_imbedded_EI*grid_annual_sum_MWh/h2prod_annual_sum) + ely_stack_capex_EI# kg CO2e/kg H2
            electrolysis_Scope2_EI = scope2_grid_emissions_annual_sum/h2prod_annual_sum 
            electrolysis_Scope1_EI = 0
            electrolysis_total_EI = electrolysis_Scope1_EI + electrolysis_Scope2_EI + electrolysis_Scope3_EI
            # Calculate ammonia emissions via grid only electrolysis
            NH3_electrolysis_Scope3_EI = NH3_H2_consume * electrolysis_total_EI + NH3_PO_consume * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + NH3_PO_consume * grid_imbedded_EI * g_to_kg_conv
            NH3_electrolysis_Scope2_EI = NH3_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv
            NH3_electrolysis_Scope1_EI = NH3_boiler_EI
            NH3_electrolysis_total_EI  = NH3_electrolysis_Scope1_EI + NH3_electrolysis_Scope2_EI + NH3_electrolysis_Scope3_EI
            # Calculate steel emissions via grid only electrolysis
            steel_electrolysis_Scope3_EI = (steel_H2_consume * electrolysis_total_EI * MT_to_kg_conv + steel_lime_EI * steel_lime_consume * MT_to_kg_conv + steel_iron_ore_EI  * steel_iron_ore_consume * MT_to_kg_conv + steel_NG_supply_EI * steel_NG_consume  + cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * steel_PO_consume + steel_H2O_EI * steel_H2O_consume * gal_to_ton_conv) + steel_PO_consume  * grid_imbedded_EI * g_to_kg_conv  # kg CO2e/metric tonne steel
            steel_electrolysis_Scope2_EI = steel_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean()  
            steel_electrolysis_Scope1_EI = steel_CH4_prod + steel_CO2_prod
            steel_electrolysis_total_EI  = steel_electrolysis_Scope1_EI + steel_electrolysis_Scope2_EI + steel_electrolysis_Scope3_EI
        if 'off-grid' in grid_case:
            # Calculate renewable only electrolysis emissions        
            electrolysis_Scope3_EI = (wind_capex_EI*hopp_finsum['Wind annual energy (MWh)'].values.tolist()[0] + solar_pv_capex_EI*hopp_finsum['Solar annual energy (MWh)'].values.tolist()[0])/h2prod_annual_sum + ely_stack_capex_EI # kg CO2e/kg H2
            electrolysis_Scope2_EI = 0
            electrolysis_Scope1_EI = 0
            electrolysis_total_EI = electrolysis_Scope1_EI + electrolysis_Scope2_EI + electrolysis_Scope3_EI
            electrolysis_total_EI_policy_offgrid = electrolysis_total_EI
            electrolysis_total_EI_policy_grid = 0
            # Calculate ammonia emissions via renewable electrolysis
            NH3_electrolysis_Scope3_EI = NH3_H2_consume * electrolysis_total_EI + NH3_PO_consume * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv + NH3_PO_consume * grid_imbedded_EI * g_to_kg_conv
            NH3_electrolysis_Scope2_EI = NH3_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv
            NH3_electrolysis_Scope1_EI = NH3_boiler_EI
            NH3_electrolysis_total_EI = NH3_electrolysis_Scope1_EI + NH3_electrolysis_Scope2_EI + NH3_electrolysis_Scope3_EI
            # Calculate steel emissions via renewable electrolysis
            steel_electrolysis_Scope3_EI = (steel_H2_consume * electrolysis_total_EI * MT_to_kg_conv + steel_lime_EI * steel_lime_consume * MT_to_kg_conv + steel_iron_ore_EI  * steel_iron_ore_consume * MT_to_kg_conv + steel_NG_supply_EI * steel_NG_consume  + cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * steel_PO_consume + steel_H2O_EI * steel_H2O_consume * gal_to_ton_conv) + steel_PO_consume  * grid_imbedded_EI * g_to_kg_conv  # kg CO2e/metric tonne steel
            steel_electrolysis_Scope2_EI = steel_PO_consume * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() 
            steel_electrolysis_Scope1_EI = steel_CH4_prod + steel_CO2_prod
            steel_electrolysis_total_EI  = steel_electrolysis_Scope1_EI + steel_electrolysis_Scope2_EI + steel_electrolysis_Scope3_EI

        electrolysis_Scope3_emission_intensity.append(electrolysis_Scope3_EI)
        electrolysis_Scope2_emission_intensity.append(electrolysis_Scope2_EI)
        electrolysis_emission_intensity.append(electrolysis_total_EI)
        smr_Scope3_emission_intensity.append(smr_Scope3_EI)
        smr_Scope2_emission_intensity.append(smr_Scope2_EI)
        smr_emission_intensity.append(smr_total_EI)
        smr_ccs_Scope3_emission_intensity.append(smr_Scope3_EI)
        smr_ccs_Scope2_emission_intensity.append(smr_Scope2_EI)
        smr_ccs_emission_intensity.append(smr_ccs_total_EI)
        atr_ccs_Scope3_emission_intensity.append(atr_ccs_Scope3_EI)
        atr_ccs_Scope2_emission_intensity.append(atr_ccs_Scope2_EI)
        atr_ccs_emission_intensity.append(atr_ccs_total_EI)
        NH3_electrolysis_Scope3_emission_intensity.append(NH3_electrolysis_Scope3_EI)
        NH3_electrolysis_Scope2_emission_intensity.append(NH3_electrolysis_Scope2_EI)
        NH3_electrolysis_emission_intensity.append(NH3_electrolysis_total_EI)
        steel_electrolysis_Scope3_emission_intensity.append(steel_electrolysis_Scope3_EI)
        steel_electrolysis_Scope2_emission_intensity.append(steel_electrolysis_Scope2_EI)
        steel_electrolysis_emission_intensity.append(steel_electrolysis_total_EI)
        NH3_smr_Scope3_emission_intensity.append(NH3_smr_Scope3_EI)
        NH3_smr_Scope2_emission_intensity.append(NH3_smr_Scope2_EI)
        NH3_smr_emission_intensity.append(NH3_smr_total_EI)
        steel_smr_Scope3_emission_intensity.append(steel_smr_Scope3_EI)
        steel_smr_Scope2_emission_intensity.append(steel_smr_Scope2_EI)
        steel_smr_emission_intensity.append(steel_smr_total_EI)
        NH3_smr_ccs_Scope3_emission_intensity.append(NH3_smr_ccs_Scope3_EI)
        NH3_smr_ccs_Scope2_emission_intensity.append(NH3_smr_ccs_Scope2_EI)
        NH3_smr_ccs_emission_intensity.append(NH3_smr_ccs_total_EI)
        steel_smr_ccs_Scope3_emission_intensity.append(steel_smr_ccs_Scope3_EI)
        steel_smr_ccs_Scope2_emission_intensity.append(steel_smr_ccs_Scope2_EI)
        steel_smr_ccs_emission_intensity.append(steel_smr_ccs_total_EI)        
        NH3_atr_ccs_Scope3_emission_intensity.append(NH3_atr_ccs_Scope3_EI)
        NH3_atr_ccs_Scope2_emission_intensity.append(NH3_atr_ccs_Scope2_EI)
        NH3_atr_ccs_emission_intensity.append(NH3_atr_ccs_total_EI)
        steel_atr_ccs_Scope3_emission_intensity.append(steel_atr_ccs_Scope3_EI)
        steel_atr_ccs_Scope2_emission_intensity.append(steel_atr_ccs_Scope2_EI)
        steel_atr_ccs_emission_intensity.append(steel_atr_ccs_total_EI)
        
    emission_intensities_df = pd.DataFrame({'Year':years,
                                            'electrolysis Scope3 EI (kg CO2e/kg H2)':electrolysis_Scope3_emission_intensity, 
                                            'electrolysis Scope2 EI (kg CO2e/kg H2)':electrolysis_Scope2_emission_intensity, 
                                            'electrolysis EI (kg CO2e/kg H2)':electrolysis_emission_intensity, 
                                            'smr Scope3 EI (kg CO2e/kg H2)': smr_Scope3_emission_intensity, 
                                            'smr Scope2 EI (kg CO2e/kg H2)': smr_Scope2_emission_intensity, 
                                            'smr EI (kg CO2e/kg H2)': smr_emission_intensity, 
                                            'smr ccs Scope3 EI (kg CO2e/kg H2)': smr_ccs_Scope3_emission_intensity, 
                                            'smr ccs Scope2 EI (kg CO2e/kg H2)': smr_ccs_Scope2_emission_intensity, 
                                            'smr ccs EI (kg CO2e/kg H2)': smr_ccs_emission_intensity,      
                                            'atr ccs Scope3 EI (kg CO2e/kg H2)': atr_ccs_Scope3_emission_intensity, 
                                            'atr ccs Scope2 EI (kg CO2e/kg H2)': atr_ccs_Scope2_emission_intensity, 
                                            'atr ccs EI (kg CO2e/kg H2)': atr_ccs_emission_intensity,  
                                            'NH3 electrolysis Scope3 EI (kg CO2e/kg H2)': NH3_electrolysis_Scope3_emission_intensity, 
                                            'NH3 electrolysis Scope2 EI (kg CO2e/kg H2)': NH3_electrolysis_Scope2_emission_intensity, 
                                            'NH3 electrolysis EI (kg CO2e/kg H2)': NH3_electrolysis_emission_intensity, 
                                            'steel electrolysis Scope3 EI (kg CO2e/kg H2)': steel_electrolysis_Scope3_emission_intensity, 
                                            'steel electrolysis Scope2 EI (kg CO2e/kg H2)': steel_electrolysis_Scope2_emission_intensity, 
                                            'steel electrolysis EI (kg CO2e/kg H2)': steel_electrolysis_emission_intensity,
                                            'NH3 smr Scope3 EI (kg CO2e/kg H2)': NH3_smr_Scope3_emission_intensity, 
                                            'NH3 smr Scope2 EI (kg CO2e/kg H2)': NH3_smr_Scope2_emission_intensity, 
                                            'NH3 smr EI (kg CO2e/kg H2)': NH3_smr_emission_intensity, 
                                            'steel smr Scope3 EI (kg CO2e/kg H2)': steel_smr_Scope3_emission_intensity, 
                                            'steel smr Scope2 EI (kg CO2e/kg H2)': steel_smr_Scope2_emission_intensity, 
                                            'steel smr EI (kg CO2e/kg H2)': steel_smr_emission_intensity,
                                            'NH3 smr ccs Scope3 EI (kg CO2e/kg H2)': NH3_smr_ccs_Scope3_emission_intensity, 
                                            'NH3 smr ccs Scope2 EI (kg CO2e/kg H2)': NH3_smr_ccs_Scope2_emission_intensity, 
                                            'NH3 smr ccs EI (kg CO2e/kg H2)': NH3_smr_ccs_emission_intensity, 
                                            'steel smr ccs Scope3 EI (kg CO2e/kg H2)': steel_smr_ccs_Scope3_emission_intensity, 
                                            'steel smr ccs Scope2 EI (kg CO2e/kg H2)': steel_smr_ccs_Scope2_emission_intensity, 
                                            'steel smr ccs EI (kg CO2e/kg H2)': steel_smr_ccs_emission_intensity,
                                            'NH3 atr ccs Scope3 EI (kg CO2e/kg H2)': NH3_atr_ccs_Scope3_emission_intensity, 
                                            'NH3 atr ccs Scope2 EI (kg CO2e/kg H2)': NH3_atr_ccs_Scope2_emission_intensity, 
                                            'NH3 atr ccs EI (kg CO2e/kg H2)': NH3_atr_ccs_emission_intensity, 
                                            'steel atr ccs Scope3 EI (kg CO2e/kg H2)': steel_atr_ccs_Scope3_emission_intensity, 
                                            'steel atr ccs Scope2 EI (kg CO2e/kg H2)': steel_atr_ccs_Scope2_emission_intensity, 
                                            'steel atr ccs EI (kg CO2e/kg H2)': steel_atr_ccs_emission_intensity,
                                            })

    endoflife_year = cambium_year + system_life

    electrolysis_Scope3_EI_interpolated = []
    electrolysis_Scope2_EI_interpolated = []
    electrolysis_EI_interpolated = []
    smr_Scope3_EI_interpolated = []
    smr_Scope2_EI_interpolated = []
    smr_EI_interpolated = []
    smr_ccs_Scope3_EI_interpolated = []
    smr_ccs_Scope2_EI_interpolated = []
    smr_ccs_EI_interpolated = []
    atr_ccs_Scope3_EI_interpolated = []
    atr_ccs_Scope2_EI_interpolated = []
    atr_ccs_EI_interpolated = []
    NH3_electrolysis_Scope3_EI_interpolated = []
    NH3_electrolysis_Scope2_EI_interpolated = []
    NH3_electrolysis_EI_interpolated = []
    steel_electrolysis_Scope3_EI_interpolated = []
    steel_electrolysis_Scope2_EI_interpolated = []
    steel_electrolysis_EI_interpolated = []
    NH3_smr_Scope3_EI_interpolated = []
    NH3_smr_Scope2_EI_interpolated = []
    NH3_smr_EI_interpolated = []
    steel_smr_Scope3_EI_interpolated = []
    steel_smr_Scope2_EI_interpolated = []
    steel_smr_EI_interpolated = []
    NH3_smr_ccs_Scope3_EI_interpolated = []
    NH3_smr_ccs_Scope2_EI_interpolated = []
    NH3_smr_ccs_EI_interpolated = []
    steel_smr_ccs_Scope3_EI_interpolated = []
    steel_smr_ccs_Scope2_EI_interpolated = []
    steel_smr_ccs_EI_interpolated = []
    NH3_atr_ccs_Scope3_EI_interpolated = []
    NH3_atr_ccs_Scope2_EI_interpolated = []
    NH3_atr_ccs_EI_interpolated = []
    steel_atr_ccs_Scope3_EI_interpolated = []
    steel_atr_ccs_Scope2_EI_interpolated = []
    steel_atr_ccs_EI_interpolated = []
    
    for year in range(cambium_year,endoflife_year):
       if year <= max(emission_intensities_df['Year']):
           electrolysis_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['electrolysis Scope3 EI (kg CO2e/kg H2)']))
           electrolysis_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['electrolysis Scope2 EI (kg CO2e/kg H2)']))
           electrolysis_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['electrolysis EI (kg CO2e/kg H2)']))
           smr_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['smr Scope3 EI (kg CO2e/kg H2)']))
           smr_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['smr Scope2 EI (kg CO2e/kg H2)']))
           smr_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['smr EI (kg CO2e/kg H2)']))
           smr_ccs_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['smr ccs Scope3 EI (kg CO2e/kg H2)']))
           smr_ccs_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['smr ccs Scope2 EI (kg CO2e/kg H2)']))
           smr_ccs_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['smr ccs EI (kg CO2e/kg H2)']))           
           atr_ccs_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr ccs Scope3 EI (kg CO2e/kg H2)']))
           atr_ccs_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr ccs Scope2 EI (kg CO2e/kg H2)']))
           atr_ccs_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr ccs EI (kg CO2e/kg H2)']))                      
           NH3_electrolysis_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 electrolysis Scope3 EI (kg CO2e/kg H2)']))
           NH3_electrolysis_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 electrolysis Scope2 EI (kg CO2e/kg H2)']))
           NH3_electrolysis_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 electrolysis EI (kg CO2e/kg H2)']))
           steel_electrolysis_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel electrolysis Scope3 EI (kg CO2e/kg H2)']))
           steel_electrolysis_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel electrolysis Scope2 EI (kg CO2e/kg H2)']))
           steel_electrolysis_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel electrolysis EI (kg CO2e/kg H2)']))
           NH3_smr_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 smr Scope3 EI (kg CO2e/kg H2)']))
           NH3_smr_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 smr Scope2 EI (kg CO2e/kg H2)']))
           NH3_smr_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 smr EI (kg CO2e/kg H2)']))
           steel_smr_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel smr Scope3 EI (kg CO2e/kg H2)']))
           steel_smr_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel smr Scope2 EI (kg CO2e/kg H2)']))
           steel_smr_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel smr EI (kg CO2e/kg H2)']))  
           NH3_smr_ccs_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 smr ccs Scope3 EI (kg CO2e/kg H2)']))
           NH3_smr_ccs_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 smr ccs Scope2 EI (kg CO2e/kg H2)']))
           NH3_smr_ccs_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 smr ccs EI (kg CO2e/kg H2)']))
           steel_smr_ccs_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel smr ccs Scope3 EI (kg CO2e/kg H2)']))
           steel_smr_ccs_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel smr ccs Scope2 EI (kg CO2e/kg H2)']))
           steel_smr_ccs_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel smr ccs EI (kg CO2e/kg H2)']))  
           NH3_atr_ccs_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 atr ccs Scope3 EI (kg CO2e/kg H2)']))
           NH3_atr_ccs_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 atr ccs Scope2 EI (kg CO2e/kg H2)']))
           NH3_atr_ccs_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['NH3 atr ccs EI (kg CO2e/kg H2)']))
           steel_atr_ccs_Scope3_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel atr ccs Scope3 EI (kg CO2e/kg H2)']))
           steel_atr_ccs_Scope2_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel atr ccs Scope2 EI (kg CO2e/kg H2)']))
           steel_atr_ccs_EI_interpolated.append(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['steel atr ccs EI (kg CO2e/kg H2)']))  
       else:
           electrolysis_Scope3_EI_interpolated.append(emission_intensities_df['electrolysis Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           electrolysis_Scope2_EI_interpolated.append(emission_intensities_df['electrolysis Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           electrolysis_EI_interpolated.append(emission_intensities_df['electrolysis EI (kg CO2e/kg H2)'].values[-1:][0])
           smr_Scope3_EI_interpolated.append(emission_intensities_df['smr Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           smr_Scope2_EI_interpolated.append(emission_intensities_df['smr Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           smr_EI_interpolated.append(emission_intensities_df['smr EI (kg CO2e/kg H2)'].values[-1:][0])
           smr_ccs_Scope3_EI_interpolated.append(emission_intensities_df['smr ccs Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           smr_ccs_Scope2_EI_interpolated.append(emission_intensities_df['smr ccs Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           smr_ccs_EI_interpolated.append(emission_intensities_df['smr ccs EI (kg CO2e/kg H2)'].values[-1:][0])
           atr_ccs_Scope3_EI_interpolated.append(emission_intensities_df['atr ccs Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           atr_ccs_Scope2_EI_interpolated.append(emission_intensities_df['atr ccs Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           atr_ccs_EI_interpolated.append(emission_intensities_df['atr ccs EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_electrolysis_Scope3_EI_interpolated.append(emission_intensities_df['NH3 electrolysis Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_electrolysis_Scope2_EI_interpolated.append(emission_intensities_df['NH3 electrolysis Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_electrolysis_EI_interpolated.append(emission_intensities_df['NH3 electrolysis EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_electrolysis_Scope3_EI_interpolated.append(emission_intensities_df['steel electrolysis Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_electrolysis_Scope2_EI_interpolated.append(emission_intensities_df['steel electrolysis Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_electrolysis_EI_interpolated.append(emission_intensities_df['steel electrolysis EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_smr_Scope3_EI_interpolated.append(emission_intensities_df['NH3 smr Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_smr_Scope2_EI_interpolated.append(emission_intensities_df['NH3 smr Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_smr_EI_interpolated.append(emission_intensities_df['NH3 smr EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_smr_Scope3_EI_interpolated.append(emission_intensities_df['steel smr Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_smr_Scope2_EI_interpolated.append(emission_intensities_df['steel smr Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_smr_EI_interpolated.append(emission_intensities_df['steel smr EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_smr_ccs_Scope3_EI_interpolated.append(emission_intensities_df['NH3 smr ccs Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_smr_ccs_Scope2_EI_interpolated.append(emission_intensities_df['NH3 smr ccs Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_smr_ccs_EI_interpolated.append(emission_intensities_df['NH3 smr ccs EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_smr_ccs_Scope3_EI_interpolated.append(emission_intensities_df['steel smr ccs Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_smr_ccs_Scope2_EI_interpolated.append(emission_intensities_df['steel smr ccs Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_smr_ccs_EI_interpolated.append(emission_intensities_df['steel smr ccs EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_atr_ccs_Scope3_EI_interpolated.append(emission_intensities_df['NH3 atr ccs Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_atr_ccs_Scope2_EI_interpolated.append(emission_intensities_df['NH3 atr ccs Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           NH3_atr_ccs_EI_interpolated.append(emission_intensities_df['NH3 atr ccs EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_atr_ccs_Scope3_EI_interpolated.append(emission_intensities_df['steel atr ccs Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_atr_ccs_Scope2_EI_interpolated.append(emission_intensities_df['steel atr ccs Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           steel_atr_ccs_EI_interpolated.append(emission_intensities_df['steel atr ccs EI (kg CO2e/kg H2)'].values[-1:][0])
      # print(smr_EI_interpolated)
    
    electrolysis_Scope3_LCA = sum(np.asarray(electrolysis_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    electrolysis_Scope2_LCA = sum(np.asarray(electrolysis_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    electrolysis_total_LCA = sum(np.asarray(electrolysis_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    smr_Scope3_LCA = sum(np.asarray(smr_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    smr_Scope2_LCA = sum(np.asarray(smr_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    smr_total_LCA = sum(np.asarray(smr_EI_interpolated) * h2prod_annual_sum)/h2prod_life_sum
    smr_ccs_Scope3_LCA = sum(np.asarray(smr_ccs_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    smr_ccs_Scope2_LCA = sum(np.asarray(smr_ccs_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    smr_ccs_total_LCA = sum(np.asarray(smr_ccs_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    atr_ccs_Scope3_LCA = sum(np.asarray(atr_ccs_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    atr_ccs_Scope2_LCA = sum(np.asarray(atr_ccs_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    atr_ccs_total_LCA = sum(np.asarray(atr_ccs_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_electrolysis_Scope3_LCA = sum(np.asarray(NH3_electrolysis_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_electrolysis_Scope2_LCA = sum(np.asarray(NH3_electrolysis_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_electrolysis_total_LCA = sum(np.asarray(NH3_electrolysis_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_electrolysis_Scope3_LCA = sum(np.asarray(steel_electrolysis_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_electrolysis_Scope2_LCA = sum(np.asarray(steel_electrolysis_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_electrolysis_total_LCA = sum(np.asarray(steel_electrolysis_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_smr_Scope3_LCA = sum(np.asarray(NH3_smr_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_smr_Scope2_LCA = sum(np.asarray(NH3_smr_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_smr_total_LCA = sum(np.asarray(NH3_smr_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_smr_Scope3_LCA = sum(np.asarray(steel_smr_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_smr_Scope2_LCA = sum(np.asarray(steel_smr_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_smr_total_LCA = sum(np.asarray(steel_smr_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_smr_ccs_Scope3_LCA = sum(np.asarray(NH3_smr_ccs_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_smr_ccs_Scope2_LCA = sum(np.asarray(NH3_smr_ccs_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_smr_ccs_total_LCA = sum(np.asarray(NH3_smr_ccs_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_smr_ccs_Scope3_LCA = sum(np.asarray(steel_smr_ccs_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_smr_ccs_Scope2_LCA = sum(np.asarray(steel_smr_ccs_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_smr_ccs_total_LCA = sum(np.asarray(steel_smr_ccs_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum    
    NH3_atr_ccs_Scope3_LCA = sum(np.asarray(NH3_atr_ccs_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_atr_ccs_Scope2_LCA = sum(np.asarray(NH3_atr_ccs_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    NH3_atr_ccs_total_LCA = sum(np.asarray(NH3_atr_ccs_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_atr_ccs_Scope3_LCA = sum(np.asarray(steel_atr_ccs_Scope3_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_atr_ccs_Scope2_LCA = sum(np.asarray(steel_atr_ccs_Scope2_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
    steel_atr_ccs_total_LCA = sum(np.asarray(steel_atr_ccs_EI_interpolated) * h2prod_annual_sum) /h2prod_life_sum
                    
    '''
    For reference:s
        Steel production with DRI using 100% natural gas has GHG emissions of ~1.8 kg CO2e/kg steel according to GREET 2022.
        Steel production with DRI using 100% clean hydrogen has GHG emissions of ~0.8 kg CO2e/kg hydrogen according to GREET 2022.
        For virgin steel production, we expect GHG around ~2,750 kg CO2e/ton steel (we are not using that case)
        Using 100% H2 (clean H2) in EAF, GHG should be ~260 kg CO2e/ton steel
    '''
    
    # Put all cumulative metrics into a dictionary, and then a dataframe
    d = {'Total Life Cycle H2 Production (tonnes-H2/MW)': [h2prod_annual_sum],'Total Scope 2 (Combustion) GHG Emissions (tonnes-CO2e/MW)': [scope2_grid_emissions_annual_sum],
          'Total Scope 3 (Production) GHG Emissions (tonnes-CO2e/MW)': [scope3_grid_emissions_annual_sum],'Total Life Cycle Emissions (tonnes-CO2e/MW)' : [total_grid_emissions_annual_sum],
          'Annaul Average Grid Emission Intensity (kg-CO2/MWh)': [grid_emission_intensity_annual_average],
          'SMR Scope 3 GHG Emissions (kg-CO2e/kg-H2)': [smr_Scope3_LCA],'SMR Scope 2 GHG Emissions (kg-CO2e/kg-H2)': [smr_Scope2_LCA],
          'SMR Scope 1 GHG Emissions (kg-CO2e/kg-H2)': [smr_Scope1_EI],
          #'SMR Total GHG Emissions (kg-CO2e/kg-H2)': [smr_total_EI],  
          'SMR Total GHG Emissions (kg-CO2e/kg-H2)': [smr_total_LCA], 
          'Ammonia SMR Scope 3 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_Scope3_LCA],
          'Ammonia SMR Scope 2 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_Scope2_LCA], 
          'Ammonia SMR Scope 1 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_Scope1_EI],
          #'Ammonia SMR Total GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_total_EI], 
          'Ammonia SMR Total GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_total_LCA], 
          'Steel SMR Scope 3 GHG Emissions (kg-CO2e/MT steel)': [steel_smr_Scope3_LCA],
          'Steel SMR Scope 2 GHG Emissions (kg-CO2e/MT steel)': [steel_smr_Scope2_LCA],
          'Steel SMR Scope 1 GHG Emissions (kg-CO2e/MT steel)': [steel_smr_Scope1_EI],
          #'Steel SMR Total GHG Emissions (kg-CO2e/MT steel)': [steel_smr_total_EI],    
          'Steel SMR Total GHG Emissions (kg-CO2e/MT steel)': [steel_smr_total_LCA],  
          'SMR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-H2)': [smr_ccs_Scope3_LCA],
          'SMR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-H2)': [smr_ccs_Scope2_LCA],
          'SMR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-H2)': [smr_ccs_Scope1_EI],
          #'SMR with CCS Total GHG Emissions (kg-CO2e/kg-H2)': [smr_ccs_total_EI],     
          'SMR with CCS Total GHG Emissions (kg-CO2e/kg-H2)': [smr_ccs_total_LCA],   
          'Ammonia SMR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_ccs_Scope3_LCA],
          'Ammonia SMR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_ccs_Scope2_LCA], 
          'Ammonia SMR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_ccs_Scope1_EI],
          #'Ammonia SMR with CCS Total GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_ccs_total_EI],    
          'Ammonia SMR with CCS Total GHG Emissions (kg-CO2e/kg-NH3)': [NH3_smr_ccs_total_LCA], 
          'Steel SMR with CCS Scope 3 GHG Emissions (kg-CO2e/MT steel)': [steel_smr_ccs_Scope3_LCA],
          'Steel SMR with CCS Scope 2 GHG Emissions (kg-CO2e/MT steel)': [steel_smr_ccs_Scope2_LCA],
          'Steel SMR with CCS Scope 1 GHG Emissions (kg-CO2e/MT steel)': [steel_smr_ccs_Scope1_EI],
         # 'Steel SMR with CCS Total GHG Emissions (kg-CO2e/MT steel)': [steel_smr_ccs_total_EI],  
          'Steel SMR with CCS Total GHG Emissions (kg-CO2e/MT steel)': [steel_atr_ccs_total_LCA], 
          'ATR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-H2)': [atr_ccs_Scope3_LCA],
          'ATR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-H2)': [atr_ccs_Scope2_LCA],
          'ATR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-H2)': [atr_ccs_Scope1_EI],
          #'ATR with CCS Total GHG Emissions (kg-CO2e/kg-H2)': [atr_ccs_total_EI],     
          'ATR with CCS Total GHG Emissions (kg-CO2e/kg-H2)': [atr_ccs_total_LCA],   
          'Ammonia ATR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_atr_ccs_Scope3_LCA],
          'Ammonia ATR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_atr_ccs_Scope2_LCA], 
          'Ammonia ATR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-NH3)': [NH3_atr_ccs_Scope1_EI],
          #'Ammonia ATR with CCS Total GHG Emissions (kg-CO2e/kg-NH3)': [NH3_atr_ccs_total_EI],    
          'Ammonia ATR with CCS Total GHG Emissions (kg-CO2e/kg-NH3)': [NH3_atr_ccs_total_LCA], 
          'Steel ATR with CCS Scope 3 GHG Emissions (kg-CO2e/MT steel)': [steel_atr_ccs_Scope3_LCA],
          'Steel ATR with CCS Scope 2 GHG Emissions (kg-CO2e/MT steel)': [steel_atr_ccs_Scope2_LCA],
          'Steel ATR with CCS Scope 1 GHG Emissions (kg-CO2e/MT steel)': [steel_atr_ccs_Scope1_EI],
         # 'Steel ATR with CCS Total GHG Emissions (kg-CO2e/MT steel)': [steel_atr_ccs_total_EI],  
          'Steel ATR with CCS Total GHG Emissions (kg-CO2e/MT steel)': [steel_atr_ccs_total_LCA],                 
          'Electrolysis Scope 3 GHG Emissions (kg-CO2e/kg-H2)':[electrolysis_Scope3_LCA],
          'Electrolysis Scope 2 GHG Emissions (kg-CO2e/kg-H2)':[electrolysis_Scope2_LCA],
          'Electrolysis Scope 1 GHG Emissions (kg-CO2e/kg-H2)':[electrolysis_Scope1_EI],   
          #'Electrolysis Total GHG Emissions (kg-CO2e/kg-H2)':[electrolysis_total_EI],            
          'Electrolysis Total GHG Emissions (kg-CO2e/kg-H2)':[electrolysis_total_LCA],
          'Ammonia Electrolysis Scope 3 GHG Emissions (kg-CO2e/kg-NH3)':[NH3_electrolysis_Scope3_LCA],
          'Ammonia Electrolysis Scope 2 GHG Emissions (kg-CO2e/kg-NH3)':[NH3_electrolysis_Scope2_LCA],
          'Ammonia Electrolysis Scope 1 GHG Emissions (kg-CO2e/kg-NH3)':[NH3_electrolysis_Scope1_EI],   
          #'Ammonia Electrolysis Total GHG Emissions (kg-CO2e/kg-NH3)':[NH3_electrolysis_total_EI],     
          'Ammonia Electrolysis Total GHG Emissions (kg-CO2e/kg-NH3)':[NH3_electrolysis_total_LCA],                              
          'Steel Electrolysis Scope 3 GHG Emissions (kg-CO2e/MT steel)':[steel_electrolysis_Scope3_LCA],
          'Steel Electrolysis Scope 2 GHG Emissions (kg-CO2e/MT steel)':[steel_electrolysis_Scope2_LCA],
          'Steel Electrolysis Scope 1 GHG Emissions (kg-CO2e/MT steel)':[steel_electrolysis_Scope1_EI],   
          #'Steel Electrolysis Total GHG Emissions (kg-CO2e/MT steel)':[steel_electrolysis_total_EI]
          'Steel Electrolysis Total GHG Emissions (kg-CO2e/MT steel)':[steel_electrolysis_total_LCA]
          }
    emissionsandh2 = pd.DataFrame(data = d)
    #trial = pd.concat(emissionsandh2,ignore_index = True)
    for i1 in range(len(files2load_title_header)):
        emissionsandh2[files2load_title_header[i1]] = files2load_results_title[i0+1][i1]
    if i0 == 0:
        emissionsandh2_output = emissionsandh2
    else:
        emissionsandh2_output = pd.concat([emissionsandh2_output,emissionsandh2],ignore_index = True)
       # emissionsandh2_output = emissionsandh2_output.append(emissionsandh2,ignore_index = True)
emissionsandh2_output.to_csv(parent_path+'/Results_LCA/LCA_results.csv')
# Downselect to grid cases of interest
# emissionsandh2_output = emissionsandh2_output.loc[emissionsandh2_output['Grid Case'].isin(['grid-only-'+retail_string,'hybrid-grid-'+retail_string,'off-grid'])]

# steel_scope_1 = {}
# steel_scope_2 = {}
# steel_scope_3 = {}

# ammonia_scope_1 = {}
# ammonia_scope_2 = {}
# ammonia_scope_3 = {}

# electrolysis_cases = [
#                     #'Centralized',
#                     'Distributed'
#                     ]

# locations = [
#         'IN',
#         'TX',
#         'IA',
#         'MS',
#         'WY'
#         ]

# use_cases = [
#           #'SMR',
#           #'SMR + CCS', 
#           #'Grid Only',
#           #'Grid + Renewables',
#           'Off Grid, Centralized EC',
#           #'Off Grid, Distributed EC'
#           ]

# retail_string = 'retail-flat'

# if retail_string == 'retail-flat':
#     emissionsandh2_output  = emissionsandh2_output.loc[(emissionsandh2_output['Grid case']!='grid-only-wholesale') & (emissionsandh2_output['Grid case']!='hybrid-grid-wholesale')]
# elif retail_string == 'wholesale':
#     emissionsandh2_output = emissionsandh2_output.loc[(emissionsandh2_output['Grid case']!='grid-only-retail-flat') & (emissionsandh2_output['Grid case']!='hybrid-grid-retail-flat')]
    
# grid_cases = [
#     #'grid-only-'+retail_string,
#     #'hybrid-grid-'+retail_string,
#     'off-grid'
#     ]

# renewables_cases = [
#                     #'No-ren',
#                     'Wind',
#                     #'Wind+PV+bat'
#                     ]

# policy_options = [
#                 #'max',
#                 'no-policy'
#                 ]

# font = 'Arial'
# title_size = 10
# axis_label_size = 10
# legend_size = 6
# tick_size = 10
# resolution = 150

# years = [2020, 2025, 2030, 2035]
# years = pd.unique(years).astype(int).astype(str).tolist()  

# for electrolysis_case in electrolysis_cases:
#     for policy_option in policy_options:  
#         for grid_case in grid_cases:
#             for renewables_case in renewables_cases:
#                 emissionsandh2_plots = emissionsandh2_output.loc[(emissionsandh2_output['Electrolysis case']==electrolysis_case) & (emissionsandh2_output['Policy Option']==policy_option) & (emissionsandh2_output['Grid case']==grid_case) & (emissionsandh2_output['Renewables case']==renewables_case)]
#                 for site in locations:   
#                     for use_case in use_cases:
#                             if use_case == 'SMR':
#                                 steel_scope_1[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel SMR Scope 1 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())
#                                 steel_scope_2[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel SMR Scope 2 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())
#                                 steel_scope_3[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel SMR Scope 3 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())
#                             elif use_case == 'SMR + CCS':
#                                 steel_scope_1[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel SMR with CCS Scope 1 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())
#                                 steel_scope_2[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel SMR with CCS Scope 2 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())
#                                 steel_scope_3[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel SMR with CCS Scope 3 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())
#                             else:
#                                 #if 'grid-only' in grid_case:
#                                 steel_scope_1[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel Electrolysis Scope 1 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())
#                                 steel_scope_2[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel Electrolysis Scope 2 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())
#                                 steel_scope_3[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Steel Electrolysis Scope 3 GHG Emissions (kg-CO2e/MT steel)')].values.tolist())

#                             width = 0.5
#                             #fig, ax = plt.subplots()
#                             fig, ax = plt.subplots(1,1,figsize=(4.8,3.6), dpi= resolution)
#                             ax.bar(years,steel_scope_1[site],width,label='GHG Scope 1 Emissions',edgecolor='steelblue',color='deepskyblue')
#                             barbottom=steel_scope_1[site]
#                             ax.bar(years,steel_scope_2[site],width,bottom=barbottom,label = 'GHG Scope 2 Emissions',edgecolor='dimgray',color='dimgrey')
#                             barbottom=barbottom+steel_scope_2[site]
#                             ax.bar(years,steel_scope_3[site],width,bottom=barbottom,label='GHG Scope 3 Emissions',edgecolor='black',color='navy')
#                             barbottom=barbottom+steel_scope_3[site]
#                             #ax.axhline(y=barbottom[0], color='k', linestyle='--',linewidth=1)
                
#                             # Decorations
#                             scenario_title = site + ', ' + electrolysis_case + ', ' + grid_case + ', ' + renewables_case + ', ' + policy_option
#                             scenario_filename = site+ '_' + electrolysis_case + '_' + grid_case + '_' + renewables_case + '_' + policy_option
#                             ax.set_title(scenario_title, fontsize=title_size)
                            
#                             ax.set_ylabel('GHG (kg CO2e/MT steel)', fontname = font, fontsize = axis_label_size)
#                             #ax.set_xlabel('Scenario', fontname = font, fontsize = axis_label_size)
#                             ax.legend(fontsize = legend_size, ncol = 1, prop = {'family':'Arial','size':7})
#                             max_y = np.max(barbottom)
#                             ax.set_ylim([0,2000])
#                             ax.tick_params(axis = 'y',labelsize = 7,direction = 'in')
#                             ax.tick_params(axis = 'x',labelsize = 7,direction = 'in',rotation=45)
#                             #ax2 = ax.twinx()
#                             #ax2.set_ylim([0,10])
#                             #plt.xlim(x[0], x[-1])
#                             #plt.show()
#                             plt.tight_layout()
#                             plt.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'steelemissions_'+scenario_filename + '.png',pad_inches = 0.1)
#                             plt.close(fig = None)                           
                        
#                             if use_case == 'SMR':
#                                 ammonia_scope_1[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia SMR Scope 1 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
#                                 ammonia_scope_2[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia SMR Scope 2 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
#                                 ammonia_scope_3[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia SMR Scope 3 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
#                             elif use_case == 'SMR + CCS':
#                                 ammonia_scope_1[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia SMR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
#                                 ammonia_scope_2[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia SMR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
#                                 ammonia_scope_3[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia SMR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
#                             else:
#                                 #if 'grid-only' in grid_case:
#                                 ammonia_scope_1[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia Electrolysis Scope 1 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
#                                 ammonia_scope_2[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia Electrolysis Scope 2 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
#                                 ammonia_scope_3[site] = np.array(emissionsandh2_plots.loc[(emissionsandh2_plots['Site']==site,'Ammonia Electrolysis Scope 3 GHG Emissions (kg-CO2e/kg-NH3)')].values.tolist())
                    

#                             width = 0.5
#                             #fig, ax = plt.subplots()
#                             fig, ax = plt.subplots(1,1,figsize=(4.8,3.6), dpi= resolution)
#                             ax.bar(years,ammonia_scope_1[site],width,label='GHG Scope 1 Emissions',edgecolor='teal',color='lightseagreen')
#                             barbottom=ammonia_scope_1[site]
#                             ax.bar(years,ammonia_scope_2[site],width,bottom=barbottom,label = 'GHG Scope 2 Emissions',edgecolor='dimgray',color='grey')
#                             barbottom=barbottom+ammonia_scope_2[site]
#                             ax.bar(years,ammonia_scope_3[site],width,bottom=barbottom,label='GHG Scope 3 Emissions',edgecolor='chocolate',color='darkorange')
#                             barbottom=barbottom+ammonia_scope_3[site]
#                             #ax.axhline(y=barbottom[0], color='k', linestyle='--',linewidth=1)
                
#                             # Decorations
#                             #scenario_title = site + ', ' + use_case #+ ',' +retail_string
#                             ax.set_title(scenario_title, fontsize=title_size)
                            
#                             ax.set_ylabel('GHG (kg CO2e/kg NH3)', fontname = font, fontsize = axis_label_size)
#                             #ax.set_xlabel('Scenario', fontname = font, fontsize = axis_label_size)
#                             ax.legend(fontsize = legend_size, ncol = 1, prop = {'family':'Arial','size':7})
#                             max_y = np.max(barbottom)
#                             ax.set_ylim([0,5])
#                             ax.tick_params(axis = 'y',labelsize = 7,direction = 'in')
#                             ax.tick_params(axis = 'x',labelsize = 7,direction = 'in',rotation=45)
#                             #ax2 = ax.twinx()
#                             #ax2.set_ylim([0,10])
#                             #plt.xlim(x[0], x[-1])
#                             #plt.show()
#                             plt.tight_layout()
#                             plt.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'ammoniaemissions_'+scenario_filename + '.png',pad_inches = 0.1)
#                             plt.close(fig = None)    
#                             []
# #plt.savefig(parent_path + '/examples/H2_Analysis/LCA_results/best_GHG_steel.png')

# ### ATTENTION!!! Plotting below doesn't really work. I think we need to change the way we are doing plots
# # since we have more distinction between locations

# # years = pd.unique(emissionsandh2_output['Year']).tolist()

# # for year in years:
# #     year = 2030
# #     gridonly_emissions = emissionsandh2_output.loc[(emissionsandh2_output['Year'] == year) & (emissionsandh2_output['Grid Case'] == 'grid-only-'+retail_string)]
# #     offgrid_emissions = emissionsandh2_output.loc[(emissionsandh2_output['Year'] == year) & (emissionsandh2_output['Grid Case'] == 'off-grid') ]
# #     hybridgrid_emissions = emissionsandh2_output.loc[(emissionsandh2_output['Year'] == year) & (emissionsandh2_output['Grid Case'] == 'hybrid-grid-'+retail_string) ]

# #     smr_emissions = offgrid_emissions.drop(labels = ['Scope 1 Emissions (kg-CO2/kg-H2)','Scope 2 Emissions (kg-CO2/kg-H2)','Scope 3 Emissions (kg-CO2/kg-H2)'],axis=1)
# #     # just use IA since all are the same right now
# #     smr_emissions = smr_emissions.loc[smr_emissions['Site']=='IA'].drop(labels = ['Site'],axis=1)
# #     smr_emissions['Site'] = 'SMR - \n all sites'
# #     smr_emissions = smr_emissions.rename(columns = {'SMR Scope 3 Life Cycle Emissions (kg-CO2/kg-H2)':'Scope 3 Emissions (kg-CO2/kg-H2)','SMR Scope 2 Life Cycle Emissions (kg-CO2/kg-H2)':'Scope 2 Emissions (kg-CO2/kg-H2)',
# #                                                     'SMR Scope 1 Life Cycle Emissions (kg-CO2/kg-H2)':'Scope 1 Emissions (kg-CO2/kg-H2)'})
    
# #     # The current plotting method will not work for all grid cases; we will need to change how we do it
# #     # This at least makes it possible to compare grid-only emissions with SMR emissions
# #     aggregate_emissions = pd.concat([gridonly_emissions,smr_emissions])

# #     smr_total_emissions = aggregate_emissions.loc[aggregate_emissions['Site'] == 'SMR - \n all sites','Scope 3 Emissions (kg-CO2/kg-H2)'] + aggregate_emissions.loc[aggregate_emissions['Site'] == 'SMR - \n all sites','Scope 2 Emissions (kg-CO2/kg-H2)'] \
# #                         + aggregate_emissions.loc[aggregate_emissions['Site'] == 'SMR - \n all sites','Scope 1 Emissions (kg-CO2/kg-H2)'] 
# #     smr_total_emissions = smr_total_emissions.tolist()
# #     smr_total_emissions = smr_total_emissions[0]
    
# #     labels = pd.unique(aggregate_emissions['Site']).tolist()
    
# #     scope3 = aggregate_emissions['Scope 3 Emissions (kg-CO2/kg-H2)']
# #     scope2 = aggregate_emissions['Scope 2 Emissions (kg-CO2/kg-H2)']
# #     scope1 = aggregate_emissions['Scope 1 Emissions (kg-CO2/kg-H2)']
# #     width = 0.3
# #     fig, ax = plt.subplots()
# #     #ax.set_ylim([0, 18])
# #     ax.bar(labels, scope3, width, label = 'Scope 3 emission intensities', color = 'darkcyan')
# #     ax.bar(labels, scope2, width, bottom = scope3, label = 'Scope 2 emission intensities', color = 'darkorange')
# #     ax.bar(labels, scope1, width, bottom = scope3, label = 'Scope 1 emission intensities', color = 'goldenrod')
# #     #valuelabel(scope1, scope2, scope3, labels)
# #     ax.set_ylabel('GHG Emission Intensities (kg CO2e/kg H2)')
# #     ax.set_title('GHG Emission Intensities - All Sites ' + str(year))
# #     plt.axhline(y = smr_total_emissions, color='red', linestyle ='dashed', label = 'GHG emissions baseline')
# #     ax.legend(loc='upper right', 
# #                       #bbox_to_anchor=(0.5, 1),
# #              ncol=1, fancybox=True, shadow=False, borderaxespad=0, framealpha=0.2)
# #             #fig.tight_layout() 
# #     plt.savefig(plot_directory +'/' + plot_subdirectory +'/' +'GHG Emission Intensities_all_sites_'+str(year)+'.png', dpi = 1000)
    
# #Pull in TEA data
# # Read in the summary data from the database
# # conn = sqlite3.connect(electrolysis_directory+'Default_summary.db')
# # TEA_data = pd.read_sql_query("SELECT * From Summary",conn)

# # conn.commit()
# # conn.close()


# # TEA_data = TEA_data[['Hydrogen model','Site','Year','Turbine Size','Electrolysis case','Policy Option','Grid Case','Hydrogen annual production (kg)',\
# #                      'Steel annual production (tonne/year)','Ammonia annual production (kg/year)','LCOH ($/kg)','Steel price: Total ($/tonne)','Ammonia price: Total ($/kg)']]
# # TEA_data = TEA_data.loc[(TEA_data['Hydrogen model']=='RODeO') & (TEA_data['Grid Case'].isin(['grid-only-'+retail_string,'hybrid-grid-'+retail_string,'off-grid']))]
# # TEA_data['Year'] = TEA_data['Year'].astype(np.int32)
# # TEA_data = TEA_data.drop(labels = ['Hydrogen model'],axis =1)
# # TEA_data['Policy Option'] = TEA_data['Policy Option'].replace(' ','-')

# # # Combine data into one dataframe
# # combined_TEA_LCA_data = TEA_data.merge(emissionsandh2_output,how = 'outer', left_index = False,right_index = False)

# # # Example of calculating carbon abatement cost. 
# # # This section is mostly just to give a sense for how things like carbon abatement cost could be calculated for the above 
# # # structure
# # smr_cost_no_ccs = 1 # USD/kg-H2; just an approximation for now

# # combined_TEA_LCA_data['Total SMR Emissions (kg-CO2e/kg-H2)'] = combined_TEA_LCA_data['SMR Scope 3 GHG Emissions (kg-CO2e/kg-H2)'] +combined_TEA_LCA_data['SMR Scope 2 GHG Emissions (kg-CO2e/kg-H2)'] + combined_TEA_LCA_data['SMR Scope 1 GHG Emissions (kg-CO2e/kg-H2)']

# # combined_TEA_LCA_data['CO2 abatement cost ($/MT-CO2)'] = (combined_TEA_LCA_data['LCOH ($/kg)'] - smr_cost_no_ccs)/(combined_TEA_LCA_data['Total SMR Emissions (kg-CO2e/kg-H2)']-combined_TEA_LCA_data['Total Life Cycle Emissions (kg-CO2e/kg-H2)'])*1000

# # # Segregate data by grid scenario
# # TEALCA_data_offgrid = combined_TEA_LCA_data.loc[combined_TEA_LCA_data['Grid Case'].isin(['off-grid'])] 
# # TEALCA_data_gridonly = combined_TEA_LCA_data.loc[combined_TEA_LCA_data['Grid Case'].isin(['grid-only-'+retail_string])]
# # TEALCA_data_hybridgrid = combined_TEA_LCA_data.loc[combined_TEA_LCA_data['Grid Case'].isin(['hybrid-grid-'+retail_string])]

# # # Pivot tables for Emissions plots vs year
# # hydrogen_abatementcost_offgrid = TEALCA_data_offgrid.pivot_table(index = 'Year',columns = ['Site','Grid Case'], values = 'CO2 abatement cost ($/MT-CO2)')
# # hydrogen_abatementcost_gridonly = TEALCA_data_gridonly.pivot_table(index = 'Year',columns = ['Site','Grid Case'], values = 'CO2 abatement cost ($/MT-CO2)')
# # hydrogen_abatementcost_hybridgrid = TEALCA_data_hybridgrid.pivot_table(index = 'Year',columns = ['Site','Grid Case'], values = 'CO2 abatement cost ($/MT-CO2)')

# # # Create lists of scenario names for plot legends
# # names_gridonly = hydrogen_abatementcost_gridonly.columns.values.tolist()
# # names_gridonly_joined = []
# # for j in range(len(hydrogen_abatementcost_gridonly.columns)):
# #     names_gridonly_joined.append(', '.join(names_gridonly[j]))
    
# # names_hybridgrid = hydrogen_abatementcost_hybridgrid.columns.values.tolist()
# # names_hybridgrid_joined = []
# # for j in range(len(hydrogen_abatementcost_hybridgrid.columns)):
# #     names_hybridgrid_joined.append(', '.join(names_hybridgrid[j]))
    
# # names_offgrid = hydrogen_abatementcost_offgrid.columns.values.tolist()
# # names_offgrid_joined = []
# # for j in range(len(hydrogen_abatementcost_offgrid.columns)):
# #     names_offgrid_joined.append(', '.join(names_offgrid[j]))

# # # Abatement cost vs year
# # fig5, ax5 = plt.subplots(3,1,sharex = 'all',figsize = (4,8),dpi = 150)
# # ax5[0].plot(hydrogen_abatementcost_gridonly,marker = '.')
# # ax5[1].plot(hydrogen_abatementcost_hybridgrid,marker = '.')
# # ax5[2].plot(hydrogen_abatementcost_offgrid ,marker = '.')
# # for ax in ax5.flat:
# #     ax.tick_params(axis = 'y',labelsize = 10,direction = 'in')
# #     ax.tick_params(axis = 'x',labelsize = 10,direction = 'in',rotation = 45)
# # ax5[0].set_ylabel('Grid-Only CO2 Abatement Cost \n($/t-CO2)',fontsize = 10, fontname = 'Arial')
# # ax5[1].set_ylabel('Hybrid-Grid CO2 Abatement Cost \n($/t-CO2)',fontsize = 10, fontname='Arial')
# # ax5[2].set_ylabel('Off-Grid CO2 Abatement Cost \n($/t-CO2)',fontsize = 10, fontname = 'Arial')
# # ax5[2].set_xlabel('Year',fontsize = 10,fontname = 'Arial')
# # ax5[0].legend(names_gridonly_joined,prop = {'family':'Arial','size':6})
# # ax5[1].legend(names_hybridgrid_joined,prop = {'family':'Arial','size':6})
# # ax5[2].legend(names_offgrid_joined ,prop = {'family':'Arial','size':6})
# # plt.tight_layout()
# # plt.savefig(plot_directory +'/' + plot_subdirectory +'/' +'hydrogen_abatement_cost.png',pad_inches = 0.1)
# # plt.close(fig = None)
