# -*- coding: utf-8 -*-

# Specify file path to PyFAST
import sys
import os
import glob
#sys.path.insert(1,'../PyFAST/')
import pandas as pd
import numpy as np
import math

#sys.path.append('../PyFAST/')
#import src.PyFAST as PyFAST

import ProFAST
from grid_price_profiles import grid_price_interpolation

dir1 = os.getcwd()
dirin_el_prices = 'H2_Analysis/'
el_prices_files = glob.glob(os.path.join(dir1 + dirin_el_prices, 'annual_average_retail_prices.csv'))
#NG_costs_csv = pd.read_csv(dir1 + '\\H2_Analysis\\' + 'Green_steel_regional_NG_prices.csv', header=0,index_col=0) #2020$
#NG_costs_csv = pd.DataFrame(NG_costs_csv, columns = ['Default','Min','Max'],index = ['Indiana',"Texas","Iowa","Mississippi","Minnesota"])
dircambium = 'H2_Analysis/Cambium_data/Cambium22_MidCase100by2035_hourly_' 

def run_profast_for_hydrogen_ATR(atb_year,site_name,site_location,policy_case,NG_price_case,CCS_option,grid_price_filename):
    import numpy as np
    # Toggles
    #------------------------------------------------------------------------------
    # policy_case = 'no'
    # #policy_case = ['no', 'base', 'max']
    # CO2_credit = 0
    # atb_years = 2020 
    # #[2020,2025,2030,2035,2040]
    # site_name = "IA"
    # #["IN","TX","IA","MS"]
    # NG_price_case = 'default'
    # #['default','min','max']
   #NG_cost = 0.00536 # $2019/MJ 
    
    # Conversions
    #------------------------------------------------------------------------------
    mt_tokg_conv = 1000 # Metric tonne to kg conversion 
    hrs_in_year = 8760 # Hours in a non-leap year
    kg_to_MT_conv = 0.001 # Converion from kg to metric tonnes
    g_to_kg_conv  = 0.001  # Conversion from grams to kilograms
    kWh_to_MWh_conv = 0.001 # Conversion from kWh to MWh
    
    #------------------------------------------------------------------------------
    # Autothermal reforming (atr) - Fossil-based H2 production process
    #------------------------------------------------------------------------------

    atr_NG_combust = 56.2     # Natural gas combustion (g CO2e/MJ)
    atr_NG_consume = 167      # Natural gas consumption (MJ/kg H2); Original from H2A: 0.158 mmBtu HHV
    atr_PO_consume = 3.495    # Power consumption in atr plant (kWh/kg H2)
    atr_steam_prod = 0        # Steam production on atr site (MJ/kg H2)
    atr_HEX_eff    = 0.9      # Heat exchanger efficiency (-)
    atr_NG_supply  = 9        # Natural gas extraction and supply to atr plant assuming 2% CH4 leakage rate (g CO2e/MJ)
    ccs_perc_capture = 0.945  # Carbon capture rate (-)
    
    # Data
    #------------------------------------------------------------------------------  
    model_year_CEPCI = 816.0
    year2018_CEPCI = 603.1
    year2020_CEPCI = 596.2 
    year2022_CEPCI = 816.0
    year2008_CEPCI = 575.4
    year2011_CEPCI = 585.7 
    year2020_CPI = 271
    year2022_CPI = 292.7
    
    plant_life = 30
    land_cost = 0 # $/acre
    water_cost = 0 # $/gal H2O
    CO2_credit = {} # $/ton CO2
    #capex_desal = 
    #opex_desal = 
    capacity_factor = 0.9  
    h2_plant_capacity_kgpd = 200791 # kg H2/day
    h2_plant_capacity_kgpy = 73288715 # kg H2/yr
    hydrogen_production_kgpd = h2_plant_capacity_kgpd * capacity_factor # kg H2/day; The number is based on annual demand of 1 MMT steel; 
    hydrogen_production_kgpy = h2_plant_capacity_kgpy * capacity_factor # kg H2/year
    fom_atr_perc = 0.032 # fraction of capital cost
    electricity_cost = 0.076 # $/kWh; If electricity prices file missing, this is the cost which will be taken
    hydrogen_storage_duration = 4 # hours, which have been chosen based on RODeO runs with grid connection
    lhv_h2 = 33 # kWh/kg H2
    hhv_h2 = 39 # kWh/kg H2
    h2_HHV = 141.88 # MJ/kg H2
    water_consumption = 8.116 # gal H2O/kg H2 - for feedstock and process water
    # Get storage compressor capacity and cost
    max_h2_injection_rate_kgphr = hydrogen_production_kgpd/24
    compressor_total_capacity_kW = max_h2_injection_rate_kgphr/3600/2.0158*8641.678424

    compressor_max_capacity_kw = 16000
    n_comps = math.ceil(compressor_total_capacity_kW/compressor_max_capacity_kw)

    small_positive = 1e-6
    compressor_avg_capacity_kw = compressor_total_capacity_kW/(n_comps+small_positive)
    storage_compressor_total_installed_cost_USD = 2*n_comps*(6893.2*compressor_avg_capacity_kw**0.7464)*1.16/1.12*year2022_CEPCI/541.7

    # policy credit
    #CO2_per_H2 = 8.3 # kg CO2e/kg H2 -> change if the capture rate is changed
    CO2_per_H2 = 9.326 # From H2A
    policy_credit_45Q_duration = 12 # years
    policy_credit_PTC_duration = 10 # years
    energy_demand_process = 0 # kWh/kgH2 defaulted to atr without CCS
    energy_demand_process_ccs = 3.495 # kWh/kg H2
    total_plant_cost = 0
    NG_consumption = 167 # MJ-HHV/kgH2
    energy_demand_NG = 0
    total_energy_demand =  0 # kWh/kgH2
    CO2_TnS_unit_cost = 0
    grid_price_per_yr = []
    
    h2prod_life_sum = hydrogen_production_kgpy * plant_life
                
    if atb_year == 2022:
        cambium_year = 2030
        operational_year = 2030
    elif atb_year == 2025:
        cambium_year = 2030
        operational_year = 2030
    elif atb_year == 2030:
        cambium_year = 2035
        operational_year = 2035
    elif atb_year == 2035:
        cambium_year = 2040
        operational_year = 2040
    
    # Read in csv for grid prices
    electricity_prices= pd.read_csv('H2_Analysis/'+grid_price_filename,index_col = None,header = 0)
    elec_price = electricity_prices.loc[electricity_prices['Year']==cambium_year,site_name].tolist()[0]
    grid_prices_interpolated_USDperkwh = grid_price_interpolation(electricity_prices,site_name,atb_year,plant_life,'kWh')
    grid_cost_keys = list(grid_prices_interpolated_USDperkwh.keys())
    grid_price_per_yr = np.array(list(grid_prices_interpolated_USDperkwh.values()))
    
    # Energy demand and plant costs
    if CCS_option == 'wCCS':
        energy_demand_process_ccs = 3.495 # kWh/kgH2
        total_plant_cost = year2022_CEPCI/year2020_CEPCI * (-0.0005 * (h2_plant_capacity_kgpd**2) + 1385 * h2_plant_capacity_kgpd + 2*(10**8))  # 2022$ ; the correlation takes daily capacity
        #owners_n_catalyst_cost = 0.174 * total_plant_cost # Percentage from NETL report
        #total_plant_cost = total_plant_cost + owners_n_catalyst_cost #overnight cost
        energy_demand_NG = 0 # 2.01-1.50 # kWh/kgH2
        NG_consumption = 167 # MJ/kgH2 
        total_energy_demand = energy_demand_process_ccs + energy_demand_NG 
        CO2_captured = capacity_factor * h2_plant_capacity_kgpy * ccs_perc_capture * CO2_per_H2/1000 #tonnes CO2 per year

    elif CCS_option == 'woCCS': # this option shouldn't be used
        energy_demand_process = 0 # kWh/kgH2
        total_plant_cost = 0 # 2020$
        #owners_n_catalyst_cost = 0.174 * total_plant_cost # Percentage from NETL report
        #total_plant_cost = total_plant_cost + owners_n_catalyst_cost #overnight cost
        energy_demand_NG = 0 # 0.64-0.13 kWh/kgH2
        NG_consumption = 0 # MJ/kgH2
        total_energy_demand = energy_demand_process + energy_demand_NG    
        CO2_captured = 0
          
    # Indirect capital cost as a percentage of installed capital cost
    if site_location == 'Site 1': # Indiana
        land_cost = 7072 * year2022_CPI/year2020_CPI # $2022/acre 
        water_cost = 0.0045 * year2022_CPI/year2020_CPI #2022$/gal
        CO2_transport_capex = 7.7 * year2022_CEPCI/year2011_CEPCI #2022$/tonne CO2
        CO2_storage_capex = 8.55 * year2022_CEPCI/year2008_CEPCI #2022$/tonneCO2 Mount Simon 6 formation
    elif site_location == 'Site 2': # Texas
        land_cost = 2343 * year2022_CPI/year2020_CPI # $2022/acre
        water_cost = 0.00478 * year2022_CPI/year2020_CPI  #2022$/gal
        CO2_transport_capex = 9.35 * year2022_CEPCI/year2011_CEPCI #2022$/tonne CO2
        CO2_storage_capex = 11.87 * year2022_CEPCI/year2008_CEPCI #2022$/tonneCO2 Canyon 3 formation
    elif site_location == 'Site 3': # Iowa
        land_cost = 8310 * year2022_CPI/year2020_CPI  # $2022/acre
        water_cost = 0.00291 * year2022_CPI/year2020_CPI #2022$/gal
        CO2_transport_capex = 12.94 * year2022_CEPCI/year2011_CEPCI #2022$/tonne CO2
        CO2_storage_capex = 8.78 * year2022_CEPCI/year2008_CEPCI #2022$/tonneCO2 Mount Simon 3 formation
    elif site_location == 'Site 4': # Mississippi
        land_cost = 2652 * year2022_CPI/year2020_CPI # $2022/acre
        water_cost = 0.00409 * year2022_CPI/year2020_CPI  #2022$/gal
        CO2_transport_capex = 2.08 * year2022_CEPCI/year2011_CEPCI #2022$/tonne CO2
        CO2_storage_capex = 8.59 * year2022_CEPCI/year2008_CEPCI #2022$/tonneCO2 Lower Tuscaloosa 1 formation
    # elif site_name == 'WY': # Wyoming
    #     land_cost =751 #$2020/acre
    #     water_cost = 0.00376 # 2020$/gal
    #     electricity_cost = electricity_prices['WY'] #$/MWh
    elif site_location == 'Site 5': # Minnesota 
        land_cost = 5437 * year2022_CPI/year2020_CPI  # 2022$/acre
        water_cost=0.00291 * year2022_CPI/year2020_CPI  #2022$/gal
        CO2_transport_capex = 20.52 * year2022_CEPCI/year2011_CEPCI #2022$/tonne CO2
        CO2_storage_capex = 17.06 * year2022_CEPCI/year2008_CEPCI #2022$/tonneCO2 Basal Cambrian formation
        
    # Should connect these to something (AEO, Cambium, etc.)
    if NG_price_case == 'default':
        ngprice_filename = 'ngprices_base.csv'
    elif NG_price_case == 'max':
        ngprice_filename = 'ngprices_max.csv'
    elif NG_price_case == 'min':
        ngprice_filename = 'ngprices_min.csv'
    
    naturalgas_prices = pd.read_csv(os.path.join("H2_Analysis",ngprice_filename),index_col = None,header = 0,usecols=['Year',site_name])
    naturalgas_prices = naturalgas_prices.set_index('Year')

    #operational_year = atb_year + 5

    EOL_year = operational_year + plant_life

    # Put natural gas prices into a dictionary, keep in $/MJ
    naturalgas_prices_dict = {}
    for year in range(operational_year,EOL_year):
        naturalgas_prices_dict[year]=naturalgas_prices.loc[year,site_name]

    #------------------------------------------------------------------------------
    # CAPEX
    #------------------------------------------------------------------------------
    # Calculate storage capital costs. Storage duration arbitrarily chosen at 4 hours capacity
    if CCS_option == 'wCCS': 
        hydrogen_storage_capacity_kg = hydrogen_storage_duration * energy_demand_process_ccs * hydrogen_production_kgpy / (hrs_in_year  * hhv_h2)
        CO2_TnS_unit_cost = (CO2_transport_capex + CO2_storage_capex)* CO2_captured/(h2_plant_capacity_kgpy * capacity_factor) #$2022/kgH2
    elif CCS_option == 'woCCS': # this option shouldn't be used
        hydrogen_storage_capacity_kg = hydrogen_storage_duration * energy_demand_process * hydrogen_production_kgpy / (hrs_in_year  * hhv_h2)
        CO2_TnS_unit_cost = 0 #$2022/kgH2
       # Get hydrogen storage cost
    hydrogen_storage_capacity_MWh_HHV = hydrogen_storage_capacity_kg*h2_HHV/3600
    if hydrogen_storage_capacity_MWh_HHV <= 4085:
        base_capacity_MWh_HHV = 4085
        base_cost_USDprkg = 521.34
        scaling_factor = 0.9592
        hydrogen_storage_cost_USDprkg = year2022_CEPCI/year2020_CEPCI*base_capacity_MWh_HHV*base_cost_USDprkg*(hydrogen_storage_capacity_MWh_HHV/base_capacity_MWh_HHV)**scaling_factor/hydrogen_storage_capacity_MWh_HHV
        status_message = 'Hydrogen storage model complete'
    else:
        hydrogen_storage_cost_USDprkg = year2022_CEPCI/year2020_CEPCI*521.34
        status_message = 'Hydrogen storage model complete.\nStorage capacity: ' + str(hydrogen_storage_capacity_kg/1000) + ' metric tonnes. \nStorage cost: ' + str(hydrogen_storage_cost_USDprkg) + ' $/kg'

    capex_storage_installed = hydrogen_storage_capacity_kg * hydrogen_storage_cost_USDprkg
    capex_compressor_installed = storage_compressor_total_installed_cost_USD #compressor_capex_USDprkWe * h2_plant_capacity_kgpy * lhv_h2 / hrs_in_year 
    
    # Fixed and variable costs
    #------------------------------------------------------------------------------
    fom_atr_total = fom_atr_perc * total_plant_cost # $/year
    
    grid_cost_pr_yr_USDprkg = grid_price_per_yr*total_energy_demand
    grid_prices_interpolated_USDperkg = dict(zip(grid_cost_keys,grid_cost_pr_yr_USDprkg))
    
    #vom_atr_NG_perMJ = naturalgas_prices_dict    # $/MJ
    #other_vom_costs = 0.08938 # $/kgH2
    other_vom_costs = 0.258 * year2022_CPI/year2020_CPI # 2022$/kg H2 from H2A
    
    atr_total_EI_all = []
    atr_ccs_total_EI_all = []
    atr_Scope3_emission_intensity = []
    atr_Scope2_emission_intensity = []
    atr_emission_intensity = []
    atr_ccs_Scope3_emission_intensity = []
    atr_ccs_Scope2_emission_intensity = []
    atr_ccs_emission_intensity = []
 
    years = list(range(cambium_year,2055,5))
    for year in years:    
        # Read in Cambium data  
        cambiumdata_filepath = dircambium + site_name + '_'+str(cambium_year) + '.csv'
        cambium_data = pd.read_csv(cambiumdata_filepath,index_col = None,header = 5,usecols = ['lrmer_co2_c','lrmer_ch4_c','lrmer_n2o_c','lrmer_co2_p','lrmer_ch4_p','lrmer_n2o_p','lrmer_co2e_c','lrmer_co2e_p','lrmer_co2e'])
        
        cambium_data = cambium_data.reset_index().rename(columns = {'index':'Interval','lrmer_co2_c':'LRMER CO2 combustion (kg-CO2/MWh)','lrmer_ch4_c':'LRMER CH4 combustion (g-CH4/MWh)','lrmer_n2o_c':'LRMER N2O combustion (g-N2O/MWh)',\
                                                      'lrmer_co2_p':'LRMER CO2 production (kg-CO2/MWh)','lrmer_ch4_p':'LRMER CH4 production (g-CH4/MWh)','lrmer_n2o_p':'LRMER N2O production (g-N2O/MWh)','lrmer_co2e_c':'LRMER CO2 equiv. combustion (kg-CO2e/MWh)',\
                                                      'lrmer_co2e_p':'LRMER CO2 equiv. production (kg-CO2e/MWh)','lrmer_co2e':'LRMER CO2 equiv. total (kg-CO2e/MWh)'})
        
        cambium_data['Interval']=cambium_data['Interval']+1
        cambium_data = cambium_data.set_index('Interval')   
     
        
        # Calculate hourly grid emissions factors of interest. If we want to use different GWPs, we can do that here. The Grid Import is an hourly data i.e., in MWh
        cambium_data['Total grid emissions (kg-CO2e)'] = total_energy_demand * kWh_to_MWh_conv * hydrogen_production_kgpy * cambium_data['LRMER CO2 equiv. total (kg-CO2e/MWh)']
        cambium_data['Scope 2 (combustion) grid emissions (kg-CO2e)'] = total_energy_demand * kWh_to_MWh_conv * hydrogen_production_kgpy * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)']
        cambium_data['Scope 3 (production) grid emissions (kg-CO2e)'] = total_energy_demand * kWh_to_MWh_conv * hydrogen_production_kgpy * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)']
        
    # Calculate atr emissions
        atr_Scope3_EI = atr_NG_supply * (atr_NG_consume - atr_steam_prod/atr_HEX_eff) * g_to_kg_conv + energy_demand_process * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv # kg CO2e/kg H2
        atr_Scope2_EI = energy_demand_process * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv # kg CO2e/kg H2
        atr_Scope1_EI = atr_NG_combust * (atr_NG_consume - atr_steam_prod/atr_HEX_eff) * g_to_kg_conv # kg CO2e/kg H2
        atr_total_EI  = atr_Scope1_EI + atr_Scope2_EI + atr_Scope3_EI   
        
                   
        # Calculate atr + CCS emissions
        atr_ccs_Scope3_EI = atr_NG_supply * (atr_NG_consume - atr_steam_prod/atr_HEX_eff) * g_to_kg_conv + energy_demand_process_ccs * cambium_data['LRMER CO2 equiv. combustion (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv # kg CO2e/kg H2
        atr_ccs_Scope2_EI = energy_demand_process_ccs * cambium_data['LRMER CO2 equiv. production (kg-CO2e/MWh)'].mean() * kWh_to_MWh_conv # kg CO2e/kg H2
        atr_ccs_Scope1_EI = (1-ccs_perc_capture)* atr_NG_combust * (atr_NG_consume - atr_steam_prod/atr_HEX_eff) * g_to_kg_conv # kg CO2e/kg H2
        atr_ccs_total_EI  = atr_ccs_Scope1_EI + atr_ccs_Scope2_EI + atr_ccs_Scope3_EI  


        atr_Scope3_emission_intensity.append(atr_Scope3_EI)
        atr_Scope2_emission_intensity.append(atr_Scope2_EI)
        atr_emission_intensity.append(atr_total_EI)
        atr_ccs_Scope3_emission_intensity.append(atr_Scope3_EI)
        atr_ccs_Scope2_emission_intensity.append(atr_Scope2_EI)
        atr_ccs_emission_intensity.append(atr_ccs_total_EI)
        
    emission_intensities_df = pd.DataFrame({'Year':years,
                                            'atr Scope3 EI (kg CO2e/kg H2)': atr_Scope3_emission_intensity, 
                                            'atr Scope2 EI (kg CO2e/kg H2)': atr_Scope2_emission_intensity, 
                                            'atr EI (kg CO2e/kg H2)': atr_emission_intensity, 
                                            'atr ccs Scope3 EI (kg CO2e/kg H2)': atr_ccs_Scope3_emission_intensity, 
                                            'atr ccs Scope2 EI (kg CO2e/kg H2)': atr_ccs_Scope2_emission_intensity, 
                                            'atr ccs EI (kg CO2e/kg H2)': atr_ccs_emission_intensity
                                            })

    endoflife_year = cambium_year + plant_life

    atr_Scope3_EI_interpolated = {}
    atr_Scope2_EI_interpolated = {}
    atr_EI_interpolated = {}
    atr_ccs_Scope3_EI_interpolated = {}
    atr_ccs_Scope2_EI_interpolated = {}
    atr_ccs_EI_interpolated = {}
    
    for year in range(cambium_year,endoflife_year):
       if year <= max(emission_intensities_df['Year']):

           atr_Scope3_EI_interpolated[year]=(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr Scope3 EI (kg CO2e/kg H2)']))
           atr_Scope2_EI_interpolated[year]=(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr Scope2 EI (kg CO2e/kg H2)']))
           atr_EI_interpolated[year]=(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr EI (kg CO2e/kg H2)']))
           atr_ccs_Scope3_EI_interpolated[year]=(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr ccs Scope3 EI (kg CO2e/kg H2)']))
           atr_ccs_Scope2_EI_interpolated[year]=(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr ccs Scope2 EI (kg CO2e/kg H2)']))
           atr_ccs_EI_interpolated[year]=(np.interp(year,emission_intensities_df['Year'],emission_intensities_df['atr ccs EI (kg CO2e/kg H2)']))
   
       else:
   
           atr_Scope3_EI_interpolated[year]=(emission_intensities_df['atr Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           atr_Scope2_EI_interpolated[year]=(emission_intensities_df['atr Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           atr_EI_interpolated[year]=(emission_intensities_df['atr EI (kg CO2e/kg H2)'].values[-1:][0])
           atr_ccs_Scope3_EI_interpolated[year]=(emission_intensities_df['atr ccs Scope3 EI (kg CO2e/kg H2)'].values[-1:][0])
           atr_ccs_Scope2_EI_interpolated[year]=(emission_intensities_df['atr ccs Scope2 EI (kg CO2e/kg H2)'].values[-1:][0])
           atr_ccs_EI_interpolated[year]=(emission_intensities_df['atr ccs EI (kg CO2e/kg H2)'].values[-1:][0])         
  
    H2_PTC = {}
    CCS_credit_45Q = {}
    policy_credit = {}
    endofincentivesPTC_year = cambium_year + policy_credit_PTC_duration 
    endofincentives45Q_year = cambium_year + policy_credit_45Q_duration 
    
    for year in range(cambium_year,endofincentives45Q_year):  
        if atb_year < 2035:
            if CCS_option == 'wCCS':    
                if policy_case == 'no policy':
                    CO2_credit[year]  = 0
                elif policy_case == 'base':
                    CO2_credit[year] = 17 # $/ton CO2
                elif policy_case == 'max':
                    CO2_credit[year] = 85 # $/ton CO2             
            if CCS_option == 'woCCS':    
                if policy_case == 'no policy':
                    CO2_credit[year]  = 0
                elif policy_case == 'base':
                    CO2_credit[year] = 0 # $/ton CO2
                elif policy_case == 'max':
                    CO2_credit[year] = 0 # $/ton CO2    
                                                                 
        elif atb_year == 2035:         
            CO2_credit[year] = 0 
            CCS_credit_45Q[year] = 0
        CCS_credit_45Q[year] = CO2_credit[year] * (atr_Scope1_EI - atr_ccs_Scope1_EI)  / (mt_tokg_conv)  # $/kgH2  
        
    for year in range(cambium_year,endofincentivesPTC_year):  
        if atb_year < 2035:
    # Policy credit
            if CCS_option == 'wCCS':    
                if policy_case == 'no policy':
                    H2_PTC[year]  = 0 
                elif policy_case == 'base':
                    if atr_ccs_EI_interpolated[year] <= 0.45: # kg CO2e/kg H2
                        H2_PTC[year]  = 0.6 # $/kg H2
                    elif atr_ccs_EI_interpolated[year] > 0.45 and atr_ccs_EI_interpolated[year] <= 1.5: # kg CO2e/kg H2
                        H2_PTC[year] = 0.2 # $/kg H2
                    elif atr_ccs_EI_interpolated[year] > 1.5 and atr_ccs_EI_interpolated[year] <= 2.5: # kg CO2e/kg H2     
                        H2_PTC[year] = 0.15 # $/kg H2
                    elif atr_ccs_EI_interpolated[year] > 2.5 and atr_ccs_EI_interpolated[year] <= 4: # kg CO2e/kg H2    
                        H2_PTC[year] = 0.12 # $/kg H2
                    else:
                        H2_PTC[year]=0
                elif policy_case == 'max':                 
                    if atr_ccs_EI_interpolated[year] <= 0.45: # kg CO2e/kg H2
                        H2_PTC[year] = 3 # $/kg H2
                    elif atr_ccs_EI_interpolated[year] > 0.45 and atr_ccs_EI_interpolated[year] <= 1.5: # kg CO2e/kg H2
                        H2_PTC[year] = 1 # $/kg H2
                    elif atr_ccs_EI_interpolated[year] > 1.5 and atr_ccs_EI_interpolated[year] <= 2.5: # kg CO2e/kg H2     
                        H2_PTC[year] = 0.75 # $/kg H2
                    elif atr_ccs_EI_interpolated[year] > 2.5 and atr_ccs_EI_interpolated[year] <= 4: # kg CO2e/kg H2    
                        H2_PTC[year] = 0.6 # $/kg 
                    else:
                        H2_PTC[year]=0
            if CCS_option == 'woCCS':    
                if policy_case == 'no policy':
                    H2_PTC[year]  = 0 
                elif policy_case == 'base':
                    if atr_EI_interpolated[year] <= 0.45: # kg CO2e/kg H2
                        H2_PTC[year]  = 0.6 # $/kg H2
                    elif atr_EI_interpolated[year] > 0.45 and atr_EI_interpolated[year] <= 1.5: # kg CO2e/kg H2
                        H2_PTC[year] = 0.2 # $/kg H2
                    elif atr_EI_interpolated[year] > 1.5 and atr_EI_interpolated[year] <= 2.5: # kg CO2e/kg H2     
                        H2_PTC[year] = 0.15 # $/kg H2
                    elif atr_EI_interpolated[year] > 2.5 and atr_EI_interpolated[year] <= 4: # kg CO2e/kg H2    
                        H2_PTC[year] = 0.12 # $/kg H2
                    else:
                        H2_PTC[year]=0
                elif policy_case == 'max':             
                    if atr_EI_interpolated[year] <= 0.45: # kg CO2e/kg H2
                        H2_PTC[year] = 3 # $/kg H2
                    elif atr_EI_interpolated[year] > 0.45 and atr_EI_interpolated[year] <= 1.5: # kg CO2e/kg H2
                        H2_PTC[year] = 1 # $/kg H2
                    elif atr_EI_interpolated[year] > 1.5 and atr_EI_interpolated[year] <= 2.5: # kg CO2e/kg H2     
                        H2_PTC[year] = 0.75 # $/kg H2
                    elif atr_EI_interpolated[year] > 2.5 and atr_EI_interpolated[year] <= 4: # kg CO2e/kg H2    
                        H2_PTC[year] = 0.6 # $/kg H2   
                    else:
                        H2_PTC[year]=0
        elif atb_year == 2035:
            H2_PTC[year]=0                
                            
    #for year in range(cambium_year,endofincentivesPTC_year):
    if (sum(CCS_credit_45Q.values())  > sum(H2_PTC.values())):            
        policy_credit = CCS_credit_45Q # $/kgH2
        policy_credit_duration = policy_credit_45Q_duration
    elif (sum(CCS_credit_45Q.values())  <= sum(H2_PTC.values())): 
        policy_credit = H2_PTC # $/kgH2
    policy_credit_duration = policy_credit_PTC_duration
    
    financial_assumptions = pd.read_csv('H2_Analysis/financial_inputs.csv',index_col=None,header=0)
    financial_assumptions.set_index(["Parameter"], inplace = True)
    financial_assumptions = financial_assumptions['Hydrogen/Steel/Ammonia']

    # Set up ProFAST
    pf = ProFAST.ProFAST('blank')

    install_years = 3
    analysis_start = list(grid_prices_interpolated_USDperkwh.keys())[0] - install_years
    
    # Fill these in - can have most of them as 0 also
    gen_inflation = 0.00 # keep the zeroes after the decimal otherwise script will throw an error
    pf.set_params('commodity',{"name":'Hydrogen',"unit":"kg","initial price":10.0,"escalation":gen_inflation})
    pf.set_params('capacity',h2_plant_capacity_kgpd) #units/day
    pf.set_params('maintenance',{"value":0,"escalation":gen_inflation})
    pf.set_params('analysis start year',analysis_start)
    pf.set_params('operating life',plant_life)
    pf.set_params('installation months',36)
    pf.set_params('installation cost',{"value":0,"depr type":"Straight line","depr period":4,"depreciable":False})
    pf.set_params('non depr assets',land_cost)
    pf.set_params('end of proj sale non depr assets',land_cost*(1+gen_inflation)**plant_life)
    pf.set_params('demand rampup',0)
    pf.set_params('long term utilization',capacity_factor)
    pf.set_params('credit card fees',0)
    pf.set_params('sales tax',0) 
    pf.set_params('license and permit',{'value':00,'escalation':gen_inflation})
    pf.set_params('rent',{'value':0,'escalation':gen_inflation})
    pf.set_params('property tax and insurance',0)
    pf.set_params('admin expense',0)
    pf.set_params('total income tax rate',financial_assumptions['total income tax rate'])
    pf.set_params('capital gains tax rate',financial_assumptions['capital gains tax rate'])
    pf.set_params('sell undepreciated cap',True)
    pf.set_params('tax losses monetized',True)
    pf.set_params('general inflation rate',gen_inflation)
    pf.set_params('leverage after tax nominal discount rate',financial_assumptions['leverage after tax nominal discount rate'])
    pf.set_params('debt equity ratio of initial financing',financial_assumptions['debt equity ratio of initial financing'])
    pf.set_params('debt type','Revolving debt')
    pf.set_params('debt interest rate',financial_assumptions['debt interest rate'])
    pf.set_params('cash onhand',1)
    
    #----------------------------------- Add capital items to ProFAST ----------------
    pf.add_capital_item(name="atr Plant Cost",cost=total_plant_cost,depr_type="MACRS",depr_period=7,refurb=[0])
    pf.add_capital_item(name="Hydrogen Storage",cost=capex_storage_installed,depr_type="MACRS",depr_period=7,refurb=[0])
    pf.add_capital_item(name="Compression",cost=capex_compressor_installed,depr_type="MACRS",depr_period=7,refurb=[0])
    #    pf.add_capital_item(name ="Desalination",cost = capex_desal,depr_type="MACRS",depr_period=5,refurb=[0])
    
    total_capex = total_plant_cost+capex_storage_installed+capex_compressor_installed

    capex_fraction = {'atr Plant Cost':total_plant_cost/total_capex,
                      'Compression':capex_compressor_installed/total_capex,
                      'Hydrogen Storage':capex_storage_installed/total_capex}
    
    #-------------------------------------- Add fixed costs--------------------------------
    pf.add_fixed_cost(name="atr FOM Cost",usage=1.0,unit='$/year',cost=fom_atr_total,escalation=gen_inflation)
    #    pf.add_fixed_cost(name="Desalination Fixed O&M Cost",usage=1.0,unit='$/year',cost=opex_desal,escalation=gen_inflation)
    
    #---------------------- Add feedstocks, note the various cost options-------------------
    #pf.add_feedstock(name='Electricity',usage=total_energy_demand,unit='kWh',cost=electricity_cost,escalation=gen_inflation)
    #pf.add_feedstock(name='Natural Gas',usage=NG_consumption,unit='MJ/kg-H2',cost=NG_cost,escalation=gen_inflation)
    pf.add_feedstock(name='Water Charges',usage=water_consumption,unit='gallons of water per kg-H2',cost=water_cost,escalation=gen_inflation)
    pf.add_feedstock(name='atr NG Cost',usage=NG_consumption,unit='$/MJ',cost=naturalgas_prices_dict,escalation=gen_inflation)
    pf.add_feedstock(name='atr Electricity Cost',usage=1.0,unit='$/kg-H2',cost=grid_prices_interpolated_USDperkg,escalation=gen_inflation)
    pf.add_feedstock(name='atr VOM Cost',usage=1.0,unit='$/kg-H2',cost=other_vom_costs,escalation=gen_inflation)
    
    pf.add_incentive(name ='Policy credit', value=policy_credit, decay = 0, sunset_years = policy_credit_duration, tax_credit = True)

    sol = pf.solve_price()
    
    summary = pf.summary_vals
    
    price_breakdown = pf.get_cost_breakdown()
    
    # Calculate financial expense associated with equipment
    cap_expense = price_breakdown.loc[price_breakdown['Name']=='Repayment of debt','NPV'].tolist()[0]\
        + price_breakdown.loc[price_breakdown['Name']=='Interest expense','NPV'].tolist()[0]\
        + price_breakdown.loc[price_breakdown['Name']=='Dividends paid','NPV'].tolist()[0]\
        - price_breakdown.loc[price_breakdown['Name']=='Inflow of debt','NPV'].tolist()[0]\
        - price_breakdown.loc[price_breakdown['Name']=='Inflow of equity','NPV'].tolist()[0]    
        
    remaining_financial = price_breakdown.loc[price_breakdown['Name']=='Non-depreciable assets','NPV'].tolist()[0]\
        + price_breakdown.loc[price_breakdown['Name']=='Cash on hand reserve','NPV'].tolist()[0]\
        + price_breakdown.loc[price_breakdown['Name']=='Property insurance','NPV'].tolist()[0]\
        - price_breakdown.loc[price_breakdown['Name']=='Sale of non-depreciable assets','NPV'].tolist()[0]\
        - price_breakdown.loc[price_breakdown['Name']=='Cash on hand recovery','NPV'].tolist()[0]
    
    price_breakdown_ATR_plant = price_breakdown.loc[price_breakdown['Name']=='atr Plant Cost','NPV'].tolist()[0] + cap_expense*capex_fraction['atr Plant Cost']
    price_breakdown_H2_storage = price_breakdown.loc[price_breakdown['Name']=='Hydrogen Storage','NPV'].tolist()[0] + cap_expense*capex_fraction['Hydrogen Storage']
    price_breakdown_compression = price_breakdown.loc[price_breakdown['Name']=='Compression','NPV'].tolist()[0] + cap_expense*capex_fraction['Compression']
    #    price_breakdown_desalination = price_breakdown.loc[price_breakdown['Name']=='Desalination','NPV'].tolist()[0]
    #    price_breakdown_desalination_FOM = price_breakdown.loc[price_breakdown['Name']=='Desalination Fixed O&M Cost','NPV'].tolist()[0]

    price_breakdown_proptax_ins = price_breakdown.loc[price_breakdown['Name']=='Property insurance','NPV'].tolist()
    price_breakdown_ATR_FOM = price_breakdown.loc[price_breakdown['Name']=='atr FOM Cost','NPV'].tolist()[0]
    price_breakdown_ATR_NG = price_breakdown.loc[price_breakdown['Name']=='atr NG Cost','NPV'].tolist()[0]
    price_breakdown_ATR_E = price_breakdown.loc[price_breakdown['Name']=='atr Electricity Cost','NPV'].tolist()[0]
    price_breakdown_water_charges = price_breakdown.loc[price_breakdown['Name']=='Water Charges','NPV'].tolist()[0] 
    price_breakdown_ATR_VOM = price_breakdown.loc[price_breakdown['Name']=='atr VOM Cost','NPV'].tolist()[0]
    

    #    price_breakdown_natural_gas = price_breakdown.loc[price_breakdown['Name']=='Natural Gas','NPV'].tolist()[0]
    #    price_breakdown_electricity = price_breakdown.loc[price_breakdown['Name']=='Electricity','NPV'].tolist()[0]
    
    price_breakdown_taxes = price_breakdown.loc[price_breakdown['Name']=='Income taxes payable','NPV'].tolist()[0]\
        - price_breakdown.loc[price_breakdown['Name'] == 'Monetized tax losses','NPV'].tolist()[0]
        
    if gen_inflation > 0:
        price_breakdown_taxes = price_breakdown_taxes + price_breakdown.loc[price_breakdown['Name']=='Capital gains taxes payable','NPV'].tolist()[0]
    import numpy as np 
    # price_breakdown_financial = np.array(price_breakdown.loc[price_breakdown['Name']=='Non-depreciable assets','NPV'].tolist()[0])\
    #     + price_breakdown.loc[price_breakdown['Name']=='Cash on hand reserve','NPV'].tolist()[0]\
    #     + price_breakdown.loc[price_breakdown['Name']=='Repayment of debt','NPV'].tolist()[0]\
    #     + price_breakdown.loc[price_breakdown['Name']=='Interest expense','NPV'].tolist()[0]\
    #     + price_breakdown.loc[price_breakdown['Name']=='Dividends paid','NPV'].tolist()[0]\
    #     - price_breakdown.loc[price_breakdown['Name']=='Sale of non-depreciable assets','NPV'].tolist()[0]\
    #     - price_breakdown.loc[price_breakdown['Name']=='Cash on hand recovery','NPV'].tolist()[0]\
    #     - price_breakdown.loc[price_breakdown['Name']=='Inflow of debt','NPV'].tolist()[0]\
    #     - price_breakdown.loc[price_breakdown['Name']=='Inflow of equity','NPV'].tolist()[0]
        
    lcoh_check = price_breakdown_ATR_plant + price_breakdown_H2_storage + price_breakdown_compression \
                        + price_breakdown_ATR_FOM + price_breakdown_ATR_VOM +  price_breakdown_water_charges + price_breakdown_ATR_NG + price_breakdown_ATR_E\
                        + price_breakdown_taxes + remaining_financial + CO2_TnS_unit_cost\
                  

                       # + price_breakdown_desalination + price_breakdown_desalination_FOM
                         
    lcoh_breakdown = {'LCOH: Hydrogen Storage ($/kg)':price_breakdown_H2_storage,\
                      'LCOH: Compression ($/kg)':price_breakdown_compression,\
                      'LCOH: ATR Plant CAPEX ($/kg)':price_breakdown_ATR_plant,\
                      'LCOH: CO2 Transportation and Storage CAPEX ($/kg)':CO2_TnS_unit_cost,\
                      'LCOH: ATR Plant FOM ($/kg)':price_breakdown_ATR_FOM,\
                      'LCOH: ATR Plant VOM ($/kg)':price_breakdown_ATR_VOM,
                      'LCOH: Electricity charges ($/kg)':price_breakdown_ATR_E, 
                      'LCOH: Natural gas charges ($/kg)':price_breakdown_ATR_NG,
                      'LCOH: Taxes ($/kg)':price_breakdown_taxes,\
                      'LCOH: Water charges ($/kg)':price_breakdown_water_charges,\
                      'LCOH: Finances ($/kg)':remaining_financial,
                      'LCOH: total ($/kg)':lcoh_check}

    hydrogen_annual_production=hydrogen_production_kgpy
    levelized_cost_hydrogen = lcoh_check
    lcoe = grid_prices_interpolated_USDperkwh
    hydrogen_storage_duration_hr = hydrogen_storage_duration
    price_breakdown_storage = price_breakdown_H2_storage
    #natural_gas_cost = NG_cost

    price_breakdown = price_breakdown.drop(columns=['index','Amount'])

    return(hydrogen_annual_production, hydrogen_storage_duration_hr, levelized_cost_hydrogen, lcoh_breakdown, price_breakdown,lcoe,  plant_life,  price_breakdown_storage,price_breakdown_compression,
                         price_breakdown_ATR_plant,\
                         CO2_TnS_unit_cost,\
                         price_breakdown_ATR_FOM, price_breakdown_ATR_VOM,\
                         price_breakdown_ATR_NG, price_breakdown_ATR_E,\
                         price_breakdown_taxes,\
                         price_breakdown_water_charges,\
                         remaining_financial,\
                         total_capex
                         #policy_credit_45Q
                         )

