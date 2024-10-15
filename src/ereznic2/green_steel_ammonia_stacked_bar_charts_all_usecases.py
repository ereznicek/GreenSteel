# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolorsg
import matplotlib.ticker as ticker
import matplotlib.axes as axes
import sqlite3

# Initialization and Global Settings
#Specify directory name
electrolysis_directory = 'Results_main/Fin_sum'
sensitivity_directory = 'Results_sensitivity/Fin_sum'
smr_directory = 'Results_SMR/Fin_sum'
atr_directory = 'REsults_ATR/Fin_sum'
#plot_directory = 'Plots'
plot_directory = 'Plots-for-others'


# Retail price of interest ['retail-flat','wholesale']
retail_string = 'retail-flat'

plot_subdirectory = 'Stacked_Plots_all_technologies'

# Read in the summary data from the electrolysis case database
conn = sqlite3.connect(electrolysis_directory+'/Default_summary.db')
financial_summary_electrolysis  = pd.read_sql_query("SELECT * From Summary",conn)

conn.commit()
conn.close()

# Read in the summary data from the smr case database
conn = sqlite3.connect(smr_directory+'/Default_summary.db')
financial_summary_smr  = pd.read_sql_query("SELECT * From Summary",conn)

conn.commit()
conn.close()

# Read in the summary data from the atr case database
conn = sqlite3.connect(atr_directory+'/Default_summary.db')
financial_summary_atr  = pd.read_sql_query("SELECT * From Summary",conn)

conn.commit()
conn.close()

# Open distributed case sensitivity
# Read in the summary data from the electrolysis case database
conn = sqlite3.connect(sensitivity_directory+'/Default_summary.db')
financial_summary_electrolysis_sensitivity  = pd.read_sql_query("SELECT * From Summary",conn)

conn.commit()
conn.close()

# Narrow down to retail price of interest
if retail_string == 'retail-flat':
    financial_summary_electrolysis = financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']!='grid-only-wholesale') & (financial_summary_electrolysis['Grid case']!='hybrid-grid-wholesale')]
elif retail_string == 'wholesale':
    financial_summary_electrolysis = financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid Case']!='grid-only-retail-flat') & (financial_summary_electrolysis['Grid Case']!='hybrid-grid-retail-flat')]

# Add labels for plotting
financial_summary_smr.loc[financial_summary_smr['CCS Case']=='woCCS','Label']= 'SMR'
financial_summary_smr.loc[financial_summary_smr['CCS Case']=='woCCS','Order']= 0
financial_summary_smr.loc[financial_summary_smr['CCS Case']=='wCCS','Label']= 'SMR + CCS'
financial_summary_smr.loc[financial_summary_smr['CCS Case']=='wCCS','Order']= 1

financial_summary_atr.loc[financial_summary_atr['CCS Case']=='wCCS','Label']= 'ATR + CCS'
financial_summary_atr.loc[financial_summary_atr['CCS Case']=='wCCS','Order']= 2

financial_summary_electrolysis.loc[financial_summary_electrolysis['Grid case']=='grid-only-'+retail_string,'Label']='Grid Only'
financial_summary_electrolysis.loc[financial_summary_electrolysis['Grid case']=='grid-only-'+retail_string,'Order']= 3
#financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='hybrid-grid-'+retail_string) & (financial_summary_electrolysis['Renewables case']=='Wind'),'Label']='Grid + \n Wind'
#financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='hybrid-grid-'+retail_string) & (financial_summary_electrolysis['Renewables case']=='Wind'),'Order']=3
financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='hybrid-grid-'+retail_string) & (financial_summary_electrolysis['Renewables case']=='Wind+PV+bat'),'Label']='Grid + \n Wind + PV'
financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='hybrid-grid-'+retail_string) & (financial_summary_electrolysis['Renewables case']=='Wind+PV+bat'),'Order']=4
#financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='off-grid') & (financial_summary_electrolysis['Renewables case']=='Wind') & (financial_summary_electrolysis['Electrolysis case']=='Centralized'),'Label']='Wind Only, \n Centralized EC'
#financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='off-grid') & (financial_summary_electrolysis['Renewables case']=='Wind') & (financial_summary_electrolysis['Electrolysis case']=='Centralized'),'Order']=5
financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='off-grid') & (financial_summary_electrolysis['Renewables case']=='Wind+PV+bat') & (financial_summary_electrolysis['Electrolysis case']=='Centralized'),'Label']='Wind + PV + bat'
financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='off-grid') & (financial_summary_electrolysis['Renewables case']=='Wind+PV+bat') & (financial_summary_electrolysis['Electrolysis case']=='Centralized'),'Order']=5
#financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='off-grid') & (financial_summary_electrolysis['Renewables case']=='Wind') & (financial_summary_electrolysis['Electrolysis case']=='Distributed'),'Label']='Wind Only, \n Distributed EC'
#financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='off-grid') & (financial_summary_electrolysis['Renewables case']=='Wind') & (financial_summary_electrolysis['Electrolysis case']=='Distributed'),'Order']=7
#financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='off-grid') & (financial_summary_electrolysis['Renewables case']=='Wind+PV+bat') & (financial_summary_electrolysis['Electrolysis case']=='Distributed'),'Label']='Wind+PV+bat, \n Distributed EC'
#financial_summary_electrolysis.loc[(financial_summary_electrolysis['Grid case']=='off-grid') & (financial_summary_electrolysis['Renewables case']=='Wind+PV+bat') & (financial_summary_electrolysis['Electrolysis case']=='Distributed'),'Order']=8

# Add labels to sensitivity cases
financial_summary_electrolysis_sensitivity.loc[financial_summary_electrolysis_sensitivity['Grid case']=='grid-only-'+retail_string,'Label']='Grid Only'
financial_summary_electrolysis_sensitivity.loc[financial_summary_electrolysis_sensitivity['Grid case']=='grid-only-'+retail_string,'Order']= 3
#financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='hybrid-grid-'+retail_string) & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind'),'Label']='Grid + Wind'
#financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='hybrid-grid-'+retail_string) & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind'),'Order']=3
financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='hybrid-grid-'+retail_string) & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind+PV+bat'),'Label']='Grid + Wind + PV'
financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='hybrid-grid-'+retail_string) & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind+PV+bat'),'Order']=4
#financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='off-grid') & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind') & (financial_summary_electrolysis_sensitivity['Electrolysis case']=='Centralized'),'Label']='Wind, CE'
#financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='off-grid') & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind') & (financial_summary_electrolysis_sensitivity['Electrolysis case']=='Centralized'),'Order']=5
financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='off-grid') & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind+PV+bat') & (financial_summary_electrolysis_sensitivity['Electrolysis case']=='Centralized'),'Label']='Wind + PV + bat'
financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='off-grid') & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind+PV+bat') & (financial_summary_electrolysis_sensitivity['Electrolysis case']=='Centralized'),'Order']=5
#financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='off-grid') & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind') & (financial_summary_electrolysis_sensitivity['Electrolysis case']=='Distributed'),'Label']='Wind, DE'
#financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='off-grid') & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind') & (financial_summary_electrolysis_sensitivity['Electrolysis case']=='Distributed'),'Order']=7
#financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='off-grid') & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind+PV+bat') & (financial_summary_electrolysis_sensitivity['Electrolysis case']=='Distributed'),'Label']='Wind+PV+bat, DE'
#financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Grid case']=='off-grid') & (financial_summary_electrolysis_sensitivity['Renewables case']=='Wind+PV+bat') & (financial_summary_electrolysis_sensitivity['Electrolysis case']=='Distributed'),'Order']=8

# Rename things as necessary
financial_summary_electrolysis = financial_summary_electrolysis.rename(columns={'(-) Steel price: BOS savings ($/tonne)':'Steel price: Labor savings ($/tonne)'})
financial_summary_smr = financial_summary_smr.rename(columns={'(-) Steel price: BOS savings ($/tonne)':'Steel price: Labor savings ($/tonne)'})
financial_summary_smr.loc[financial_summary_smr['Policy Option']=='no policy','Policy Option']='no-policy'
financial_summary_atr = financial_summary_atr.rename(columns={'(-) Steel price: BOS savings ($/tonne)':'Steel price: Labor savings ($/tonne)'})
financial_summary_atr.loc[financial_summary_atr['Policy Option']=='no policy','Policy Option']='no-policy'


# Global Plot Settings
font = 'Arial'
title_size = 20
axis_label_size = 16
legend_size = 12
tick_size = 10
tickfontsize = 16
resolution = 150

locations = [
            #'IN',
            'TX',
            #'IA',
            #'MS',
            #'MN'
             ]
years = [
    #'2022',
    #'2025',
    '2030',
    #'2035'
    ]

production_cost = False
annotate_plots = True
show_arrows = True

if production_cost == True:
    plot_subdirectory = 'Stacked_Plots_all_technologies_production'

for site in locations:
    for atb_year in years:
        #site = 'TX'
        #atb_year = '2025'
        
        scenario_title = site + ', ' + atb_year
        file_name = site+'_' + atb_year
        
        # Limit to cases for specific site and year
        site_year_electrolysis = financial_summary_electrolysis.loc[(financial_summary_electrolysis['Site']==site) & (financial_summary_electrolysis['Year']==atb_year)]
        site_year_electrolysis['CCS Case'] = 'NA'
        site_year_smr = financial_summary_smr.loc[(financial_summary_smr['Site']==site) & (financial_summary_smr['Year']==atb_year)]
        site_year_smr['Electrolysis case']=  'NA'
        site_year_smr['Grid Case'] = 'NA'

        site_year_atr = financial_summary_atr.loc[(financial_summary_atr['Site']==site) & (financial_summary_atr['Year']==atb_year)]
        site_year_atr['Electrolysis case'] = 'NA'
        site_year_smr['Grid Case'] = 'NA'

        site_year_electrolysis_sensitivity = financial_summary_electrolysis_sensitivity.loc[(financial_summary_electrolysis_sensitivity['Site']==site) & (financial_summary_electrolysis_sensitivity['Year']==atb_year) & (financial_summary_electrolysis_sensitivity['Policy Option']=='no-policy')]
        site_year_electrolysis_sensitivity['CCS Case'] = 'NA'

        if production_cost == True:
            site_year_electrolysis['LCOH ($/kg)'] = site_year_electrolysis['LCOH ($/kg)'] - site_year_electrolysis['LCOH: Compression & storage ($/kg)'] - site_year_electrolysis['LCOH: Bulk H2 Transmission ($/kg)']
            site_year_electrolysis_sensitivity['LCOH ($/kg)'] = site_year_electrolysis_sensitivity['LCOH ($/kg)'] - site_year_electrolysis_sensitivity['LCOH: Compression & storage ($/kg)'] - site_year_electrolysis_sensitivity['LCOH: Bulk H2 Transmission ($/kg)']


        # Calculate SMR error bars
        site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'LCOH NG price sensitivity low ($/kg)'] = \
            site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'LCOH ($/kg)'].values - site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') &(site_year_smr['NG price case']=='min'),'LCOH ($/kg)'].values
        
        site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'LCOH NG price sensitivity high ($/kg)'] = \
            site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='max'),'LCOH ($/kg)'].values - site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') &(site_year_smr['NG price case']=='default'),'LCOH ($/kg)'].values
        
        site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'LCOS NG price sensitivity low ($/kg)'] = \
            site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'Steel price: Total ($/tonne)'].values - site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') &(site_year_smr['NG price case']=='min'),'Steel price: Total ($/tonne)'].values
        
        site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'LCOS NG price sensitivity high ($/kg)'] = \
            site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='max'),'Steel price: Total ($/tonne)'].values - site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') &(site_year_smr['NG price case']=='default'),'Steel price: Total ($/tonne)'].values
        
        site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'LCOA NG price sensitivity low ($/kg)'] = \
            site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'Ammonia price: Total ($/kg)'].values - site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') &(site_year_smr['NG price case']=='min'),'Ammonia price: Total ($/kg)'].values
        
        site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='default'),'LCOA NG price sensitivity high ($/kg)'] = \
            site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') & (site_year_smr['NG price case']=='max'),'Ammonia price: Total ($/kg)'].values - site_year_smr.loc[(site_year_smr['Policy Option']=='no-policy') &(site_year_smr['NG price case']=='default'),'Ammonia price: Total ($/kg)'].values
        
        site_year_smr = site_year_smr.loc[site_year_smr['NG price case']=='default']
        site_year_smr_sensitivity = site_year_smr.loc[site_year_smr['Policy Option']=='no-policy']

        # Calculate ATR error bars
        site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'LCOH NG price sensitivity low ($/kg)'] = \
            site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'LCOH ($/kg)'].values - site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') &(site_year_atr['NG price case']=='min'),'LCOH ($/kg)'].values
        
        site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'LCOH NG price sensitivity high ($/kg)'] = \
            site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='max'),'LCOH ($/kg)'].values - site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') &(site_year_atr['NG price case']=='default'),'LCOH ($/kg)'].values
        
        site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'LCOS NG price sensitivity low ($/kg)'] = \
            site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'Steel price: Total ($/tonne)'].values - site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') &(site_year_atr['NG price case']=='min'),'Steel price: Total ($/tonne)'].values
        
        site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'LCOS NG price sensitivity high ($/kg)'] = \
            site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='max'),'Steel price: Total ($/tonne)'].values - site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') &(site_year_atr['NG price case']=='default'),'Steel price: Total ($/tonne)'].values
        
        site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'LCOA NG price sensitivity low ($/kg)'] = \
            site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'Ammonia price: Total ($/kg)'].values - site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') &(site_year_atr['NG price case']=='min'),'Ammonia price: Total ($/kg)'].values
        
        site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='default'),'LCOA NG price sensitivity high ($/kg)'] = \
            site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') & (site_year_atr['NG price case']=='max'),'Ammonia price: Total ($/kg)'].values - site_year_atr.loc[(site_year_atr['Policy Option']=='no-policy') &(site_year_atr['NG price case']=='default'),'Ammonia price: Total ($/kg)'].values
        
        site_year_atr = site_year_atr.loc[site_year_atr['NG price case']=='default']
        site_year_atr_sensitivity = site_year_atr.loc[site_year_atr['Policy Option']=='no-policy']

        # Calculate o2/thermal integration savings
        site_year_electrolysis['Steel price: O2 Sales & Thermal Integration Savings ($/tonne)']=site_year_electrolysis['Steel price: Total ($/tonne)'] - site_year_electrolysis['Steel Price with Integration ($/tonne)']
        site_year_smr['Steel price: O2 Sales & Thermal Integration Savings ($/tonne)']=0
        site_year_atr['Steel price: O2 Sales & Thermal Integration Savings ($/tonne)']=0
        
        #Calculate LCOH policy savings
        site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','LCOH: Max policy savings ($/kg)'] = \
            site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','LCOH ($/kg)'].values - site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='max','LCOH ($/kg)'].values

        site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','LCOH: Base policy savings ($/kg)'] = \
            site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','LCOH ($/kg)'].values - site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='base','LCOH ($/kg)'].values
        
        # Calculate steel policy savings
        site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','Steel price: Max policy savings ($/tonne)'] = \
            site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','Steel price: Total ($/tonne)'].values - site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='max','Steel price: Total ($/tonne)'].values

        site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','Steel price: Base policy savings ($/tonne)'] = \
            site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','Steel price: Total ($/tonne)'].values - site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='base','Steel price: Total ($/tonne)'].values
        
        # Calculate ammonia policy savings
        site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','Ammonia price: Max policy savings ($/kg)'] = \
            site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','Ammonia price: Total ($/kg)'].values - site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='max','Ammonia price: Total ($/kg)'].values
        
        site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','Ammonia price: Base policy savings ($/kg)'] = \
            site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='no-policy','Ammonia price: Total ($/kg)'].values - site_year_electrolysis.loc[site_year_electrolysis['Policy Option']=='base','Ammonia price: Total ($/kg)'].values

        # Calculate SMR policy savings
        site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','LCOH: Max policy savings ($/kg)'] = \
            site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','LCOH ($/kg)'].values - site_year_smr.loc[site_year_smr['Policy Option']=='max','LCOH ($/kg)'].values

        site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','LCOH: Base policy savings ($/kg)'] = \
            site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','LCOH ($/kg)'].values - site_year_smr.loc[site_year_smr['Policy Option']=='base','LCOH ($/kg)'].values
        
        site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','Steel price: Max policy savings ($/tonne)'] = \
            site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','Steel price: Total ($/tonne)'].values - site_year_smr.loc[site_year_smr['Policy Option']=='max','Steel price: Total ($/tonne)'].values

        site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','Steel price: Base policy savings ($/tonne)'] = \
            site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','Steel price: Total ($/tonne)'].values - site_year_smr.loc[site_year_smr['Policy Option']=='base','Steel price: Total ($/tonne)'].values
            
        site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','Ammonia price: Max policy savings ($/kg)'] = \
            site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','Ammonia price: Total ($/kg)'].values - site_year_smr.loc[site_year_smr['Policy Option']=='max','Ammonia price: Total ($/kg)'].values

        site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','Ammonia price: Base policy savings ($/kg)'] = \
            site_year_smr.loc[site_year_smr['Policy Option']=='no-policy','Ammonia price: Total ($/kg)'].values - site_year_smr.loc[site_year_smr['Policy Option']=='base','Ammonia price: Total ($/kg)'].values
        
        # Calcualte ATR policy savings
        site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','LCOH: Max policy savings ($/kg)'] = \
            site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','LCOH ($/kg)'].values - site_year_atr.loc[site_year_atr['Policy Option']=='max','LCOH ($/kg)'].values

        site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','LCOH: Base policy savings ($/kg)'] = \
            site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','LCOH ($/kg)'].values - site_year_atr.loc[site_year_atr['Policy Option']=='base','LCOH ($/kg)'].values
        
        site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','Steel price: Max policy savings ($/tonne)'] = \
            site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','Steel price: Total ($/tonne)'].values - site_year_atr.loc[site_year_atr['Policy Option']=='max','Steel price: Total ($/tonne)'].values

        site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','Steel price: Base policy savings ($/tonne)'] = \
            site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','Steel price: Total ($/tonne)'].values - site_year_atr.loc[site_year_atr['Policy Option']=='base','Steel price: Total ($/tonne)'].values
            
        site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','Ammonia price: Max policy savings ($/kg)'] = \
            site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','Ammonia price: Total ($/kg)'].values - site_year_atr.loc[site_year_atr['Policy Option']=='max','Ammonia price: Total ($/kg)'].values

        site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','Ammonia price: Base policy savings ($/kg)'] = \
            site_year_atr.loc[site_year_atr['Policy Option']=='no-policy','Ammonia price: Total ($/kg)'].values - site_year_atr.loc[site_year_atr['Policy Option']=='base','Ammonia price: Total ($/kg)'].values
        
        # Calculate steel integration savings
        site_year_electrolysis['Steel price: Integration Savings ($/tonne)']=site_year_electrolysis['Steel price: O2 Sales & Thermal Integration Savings ($/tonne)'] + site_year_electrolysis['Steel price: Labor savings ($/tonne)']
        site_year_smr['Steel price: Integration Savings ($/tonne)']=0
        site_year_atr['Steel price: Integration Savings ($/tonne)']=0
        
        site_year_combined = pd.concat([site_year_smr,site_year_atr,site_year_electrolysis],join='inner',ignore_index=True) 
        
        # site_year_sensitivity = financial_summary_electrolysis_distributed_sensitivity.loc[(financial_summary_electrolysis_distributed_sensitivity['Site']==site) & (financial_summary_electrolysis_distributed_sensitivity['Year']==atb_year)]
        # site_year_sensitivity = site_year_sensitivity.loc[site_year_sensitivity['Policy Option']=='max']
        
        # hydrogen_error_low = site_year_combined.loc[(site_year_combined['Electrolysis case']=='Distributed') & (site_year_combined['Policy Option']=='max'),'LCOH ($/kg)'].values[0] - site_year_sensitivity['LCOH ($/kg)'].values[0]
        # steel_error_low = site_year_combined.loc[(site_year_combined['Electrolysis case']=='Distributed') & (site_year_combined['Policy Option']=='max'),'Steel price: Total ($/tonne)'].values[0] - site_year_sensitivity['Steel price: Total ($/tonne)'].values[0]
        # ammonia_error_low = site_year_combined.loc[(site_year_combined['Electrolysis case']=='Distributed') & (site_year_combined['Policy Option']=='max'),'Ammonia price: Total ($/kg)'].values[0] - site_year_sensitivity['Ammonia price: Total ($/kg)'].values[0]
         
        # hydrogen_error_low = site_year_sensitivity.loc[site_year_sensitivity['Sensitivity Case']=='high','LCOH ($/kg)'].values[0] - site_year_sensitivity.loc[site_year_sensitivity['Sensitivity Case']=='low','LCOH ($/kg)'].values[0]
        # #hydrogen_error_low = site_year_electrolysis.loc[(site_year_electrolysis['Label']=='Off Grid, \n Distributed EC') & (site_year_electrolysis['Policy Option']=='max'),'LCOH ($/kg)'].values[0] - site_year_sensitivity.loc[site_year_sensitivity['Sensitivity Case']=='low','LCOH ($/kg)'].values[0]
        
        # steel_error_low = site_year_sensitivity.loc[site_year_sensitivity['Sensitivity Case']=='high','Steel price: Total ($/tonne)'].values[0] - site_year_sensitivity.loc[site_year_sensitivity['Sensitivity Case']=='low','Steel price: Total ($/tonne)'].values[0]
        # ammonia_error_low = site_year_sensitivity.loc[site_year_sensitivity['Sensitivity Case']=='high','Ammonia price: Total ($/kg)'].values[0] - site_year_sensitivity.loc[site_year_sensitivity['Sensitivity Case']=='low','Ammonia price: Total ($/kg)'].values[0]
        # #steel_error_high = site_year_sensitivity.loc[site_year_sensitivity['Sensitivity Case']=='high','Steel price: Total ($/tonne)'].values[0] - steel_price[-1]
        
        site_year_combined = site_year_combined.loc[site_year_combined['Policy Option']=='no-policy']
        site_year_combined = site_year_combined.sort_values(by='Order',ignore_index=True)

        site_year_electrolysis_sensitivity = site_year_electrolysis_sensitivity.sort_values(by='Order',ignore_index=True)
        site_year_smr_sensitivity = site_year_smr_sensitivity.sort_values(by='Order',ignore_index = True)

               
        #steel_price = site_year_combined['Steel price: Total ($/tonne)'].values 
    
        
        #site_year_combined['Steel price: Integration Savings ($/tonne)']=site_year_combined['Steel price: O2 Sales & Thermal Integration Savings ($/tonne)'] + site_year_combined['Steel price: Labor savings ($/tonne)']
        
        #site_year_combined['Steel price: Total Savings ($/tonne)']=site_year_combined['Steel price: Policy savings ($/tonne)']+site_year_combined['Steel price: O2 Sales & Thermal Integration Savings ($/tonne)'] + site_year_combined['Steel price: Labor savings ($/tonne)']
        
        labels  = site_year_combined['Label'].values.tolist()
        
        if atb_year != '2020':
            smr_ngprice_error_low = site_year_smr_sensitivity['LCOH NG price sensitivity low ($/kg)'].values.tolist()
            smr_ngprice_error_high = site_year_smr_sensitivity['LCOH NG price sensitivity high ($/kg)'].values.tolist()

            atr_ngprice_error_low = site_year_atr_sensitivity['LCOH NG price sensitivity low ($/kg)'].values.tolist()
            atr_ngprice_error_high = site_year_atr_sensitivity['LCOH NG price sensitivity high ($/kg)'].values.tolist()

            elec_error_low = (site_year_combined.loc[(site_year_combined['Order']>2)&(site_year_combined['Policy Option']=='no-policy'),'LCOH ($/kg)'].values-site_year_electrolysis_sensitivity.loc[site_year_electrolysis_sensitivity['Electrolysis cost case']=='EC-cost-Low','LCOH ($/kg)'].values).tolist()
            elec_error_high = (site_year_electrolysis_sensitivity.loc[site_year_electrolysis_sensitivity['Electrolysis cost case']=='EC-cost-High','LCOH ($/kg)'].values-site_year_combined.loc[(site_year_combined['Order']>2)&(site_year_combined['Policy Option']=='no-policy'),'LCOH ($/kg)'].values).tolist()

            error_lcoh_low = smr_ngprice_error_low.copy()
            error_lcoh_high = smr_ngprice_error_high.copy()

            error_lcoh_low.append(atr_ngprice_error_low[0])
            error_lcoh_high.append(atr_ngprice_error_high[0])
            for j in range(len(labels)-3):
                []
                error_lcoh_low.append(max(0,elec_error_low[j]))
                error_lcoh_high.append(max(0,elec_error_high[j]))

        # error_low = []
        # error_high = []
        # for j in range(len(labels)-1):
        #     error_low.append(0)
        #     error_high.append(0)
        # error_low.append(max(0,hydrogen_error_low))
        # error_high.append(0)

        # error_high = np.array(error_high)
        # error_low = np.array(error_low)   
        
 #### # Plot hydrogen cost for all technologies - old style

        #lcoh_withpolicy = np.array(site_year_combined['LCOH ($/kg)'].values.tolist()) - np.array(site_year_combined['LCOH: Policy savings ($/kg)'].values.tolist())
        #lcoh_policy_savings = np.array(site_year_combined['LCOH: Policy savings ($/kg)'].values.tolist())
        
        # width = 0.5
        # #fig, ax = plt.subplots()
        # fig, ax = plt.subplots(1,1,figsize=(9,6), dpi= resolution)

        # #ax.bar(labels,lcoh_withpolicy,width,label='With Policy',edgecolor=['midnightblue','deepskyblue','goldenrod','darkorange','forestgreen','yellowgreen'],color=['midnightblue','deepskyblue','goldenrod','darkorange','darkgreen','yellowgreen'])
        # ax.bar(labels,lcoh_withpolicy,width,label='With Policy',edgecolor=['midnightblue','darkmagenta','goldenrod','forestgreen','darkorange','deepskyblue','darkred','cyan','salmon'],color=['midnightblue','darkmagenta','goldenrod','forestgreen','darkorange','deepskyblue','darkred','cyan','salmon'])
        # #ax.bar(labels,lcoh_withpolicy,width,label='With Policy',edgecolor=['k','k','k','k','k','k'],color=['indigo','indigo','darkgoldenrod','darkorange','darkgreen','teal'])
        # barbottom=lcoh_withpolicy
        # ax.errorbar(labels,lcoh_withpolicy,yerr=[error_low,error_high], fmt='none',elinewidth=[0,0,0,0,0,1],ecolor='none',capsize=6,markeredgewidth=1)  
        # ax.errorbar(labels[5],lcoh_withpolicy[5],yerr=[[error_low[5]],[error_high[5]]],fmt='none',elinewidth=1,capsize=6,markeredgewidth=1,ecolor='black')  
        # ax.bar(labels,lcoh_policy_savings,width,bottom=barbottom,label = 'Without policy',color='white', edgecolor = ['midnightblue','darkmagenta','goldenrod','forestgreen','darkorange','deepskyblue','darkred','cyan','salmon'],hatch='.....')
        # #ax.bar(labels,lcoh_policy_savings,width,bottom=barbottom,label = 'Without policy',color='none', edgecolor=['k','k','k','k','k','k'])
        # ax.axhline(y=0, color='k', linestyle='-',linewidth=1.5)
        # ax.axhline(y=barbottom[0], color='k', linestyle='--',linewidth=1.5)
        # barbottom = lcoh_withpolicy+lcoh_policy_savings


 #### # Plot hydrogen cost for all technologies - new style
        lcoh_nopolicy = np.array(site_year_combined['LCOH ($/kg)'].values.tolist())
        lcoh_base_policy_savings = np.array(site_year_combined['LCOH: Base policy savings ($/kg)'].values.tolist())
        lcoh_max_policy_savings = np.array(site_year_combined['LCOH: Max policy savings ($/kg)'].values.tolist())

        lcoh_nopolicy_list = site_year_combined['LCOH ($/kg)'].values.tolist()

        lcoh_nopolicy_strings = [str(round(i,2)) for i in lcoh_nopolicy_list]
        x_ax = [0,1,2,3,4,5]

        width = 0.5
        #fig, ax = plt.subplots()
        fig, ax = plt.subplots(1,1,figsize=(9,6), dpi= resolution)

        #ax.bar(labels,lcoh_nopolicy,label='Without Policy',edgecolor=['midnightblue','darkmagenta','goldenrod','forestgreen','darkorange','deepskyblue','darkred','cyan','salmon'],color=['midnightblue','darkmagenta','goldenrod','forestgreen','darkorange','deepskyblue','darkred','cyan','salmon'])
        ax.bar(labels,lcoh_nopolicy,label='Without Policy',edgecolor=['midnightblue','darkmagenta','darkred','goldenrod','forestgreen','deepskyblue'],color=['midnightblue','darkmagenta','darkred','goldenrod','forestgreen','deepskyblue'])
        if annotate_plots:
            for j in range(len(labels)):
                ax.annotate(lcoh_nopolicy_strings[j],xy=(x_ax[j]-width*3/4,lcoh_nopolicy[j]+0.15),xycoords='data',fontname = font,fontsize = 12)
        if show_arrows:
            ax.plot([0,1,2,3,4,5], lcoh_nopolicy-lcoh_base_policy_savings, color='black', marker='o', linestyle='none', markersize=3,label='Base Policy')
            ax.plot([0,1,2,3,4,5], lcoh_nopolicy-lcoh_max_policy_savings, color='dimgray', marker='s', linestyle='none', markersize=3,label='Max Policy')
        
        # Plot NG error bars
        if atb_year != '2020':
            ax.errorbar(labels,lcoh_nopolicy,yerr=[error_lcoh_low,error_lcoh_high], fmt='none',elinewidth=1.25,ecolor='dimgray',capsize=10,markeredgewidth=1.25)

        arrow_top = np.zeros(len(labels))
        ax.errorbar(labels,lcoh_nopolicy,yerr=[arrow_top,arrow_top], fmt='none',elinewidth=1,ecolor='black',capsize=10,markeredgewidth=1.25) 
        if show_arrows:
            for j in range(len(labels)): 
                ax.arrow(j,lcoh_nopolicy[j],0,-1*lcoh_base_policy_savings[j],head_width=0.1,head_length=0.25,length_includes_head=True,color='black',linestyle='-')
                ax.arrow(j,lcoh_nopolicy[j]-lcoh_base_policy_savings[j],0,-1*(lcoh_max_policy_savings[j]-lcoh_base_policy_savings[j]),head_width=0.1,head_length=0.25,length_includes_head=True,color='dimgray')
        ax.axhline(y=0, color='k', linestyle='-',linewidth=1.5)
        ax.axhline(y=lcoh_nopolicy[0], color='k', linestyle='--',linewidth=1.5)
        barbottom = lcoh_nopolicy

        # Decorations
        ax.set_title(scenario_title, fontsize=title_size)
        ax.spines[['left','top','right','bottom']].set_linewidth(1.5)
        ax.set_ylabel('Levelized  cost of hydrogen ($/kg)', fontname = font, fontsize = axis_label_size)
        #ax.set_xlabel('Scenario', fontname = font, fontsize = axis_label_size)
        ax.legend(fontsize = legend_size, ncol = 2, prop = {'family':'Arial','size':legend_size},loc='upper left')
        max_y = np.max(barbottom)
        min_y = np.min(lcoh_max_policy_savings)
        #ax.set_ylim([0,6])
        ax.set_ylim([-2,1.25*max_y])
        ax.tick_params(axis = 'y',labelsize = tickfontsize,direction = 'in',width=1.5)
        ax.tick_params(axis = 'x',labelsize = tickfontsize,direction = 'in',width=1.5,rotation=45)
        #ax2 = ax.twinx()
        #ax2.set_ylim([0,10])
        #plt.xlim(x[0], x[-1])
        plt.tight_layout()
        plt.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'lcoh_barchart_'+file_name + '_'+retail_string+'_alltechnologies.png',pad_inches = 0.1)
        plt.close(fig = None) 
        
        
        # Plot steel cost breakdown
        # error_low = []
        # error_high = []
        # for j in range(len(labels)-1):
        #     error_low.append(0)
        #     error_high.append(0)
        # error_low.append(max(0,steel_error_low))
        # error_high.append(0)

        # error_high = np.array(error_high)
        # error_low = np.array(error_low)   
        
        eaf_cap_cost = np.array(site_year_combined['Steel price: EAF and Casting CAPEX ($/tonne)'].values.tolist())
        shaftfurnace_cap_cost = np.array(site_year_combined['Steel price: Shaft Furnace CAPEX ($/tonne)'].values.tolist())
        oxsupply_cap_cost = np.array(site_year_combined['Steel price: Oxygen Supply CAPEX ($/tonne)'].values.tolist())
        h2preheat_cap_cost = np.array(site_year_combined['Steel price: H2 Pre-heating CAPEX ($/tonne)'].values.tolist())
        coolingtower_cap_cost = np.array(site_year_combined['Steel price: Cooling Tower CAPEX ($/tonne)'].values.tolist())
        piping_cap_cost = np.array(site_year_combined['Steel price: Piping CAPEX ($/tonne)'].values.tolist())
        elecinstr_cap_cost = np.array(site_year_combined['Steel price: Electrical & Instrumentation ($/tonne)'].values.tolist())
        buildingsstorwater_cap_cost = np.array(site_year_combined['Steel price: Buildings, Storage, Water Service CAPEX ($/tonne)'].values.tolist())
        misc_cap_cost = np.array(site_year_combined['Steel price: Miscellaneous CAPEX ($/tonne)'].values.tolist())
        installation_cost = np.array(site_year_combined['Steel price: Installation Cost ($/tonne)'].values.tolist())
        total_cap_cost = eaf_cap_cost+shaftfurnace_cap_cost+oxsupply_cap_cost+h2preheat_cap_cost+coolingtower_cap_cost\
            +piping_cap_cost+elecinstr_cap_cost+buildingsstorwater_cap_cost+misc_cap_cost+installation_cost\
            #-np.array(site_year_combined['Steel price: O2 Sales & Thermal Integration Savings ($/tonne)'].values.tolist())
        
        annoplabor_cost = np.array(site_year_combined['Steel price: Annual Operating Labor Cost ($/tonne)'].values.tolist())
        maintenancelabor_cost = np.array(site_year_combined['Steel price: Maintenance Labor Cost ($/tonne)'].values.tolist())
        adminsupportlabor_cost = np.array(site_year_combined['Steel price: Administrative & Support Labor Cost ($/tonne)'].values.tolist())
        fixedom_cost = annoplabor_cost+maintenancelabor_cost+adminsupportlabor_cost# - np.array(site_year_combined['Steel price: Labor savings ($/tonne)'].values.tolist())

        maintmaterials_cost = np.array(site_year_combined['Steel price: Maintenance Materials ($/tonne)'].values.tolist())
        water_cost = np.array(site_year_combined['Steel price: Raw Water Withdrawal ($/tonne)'].values.tolist())
        lime_cost = np.array(site_year_combined['Steel price: Lime ($/tonne)'].values.tolist())
        carbon_cost = np.array(site_year_combined['Steel price: Carbon ($/tonne)'].values.tolist())
        ironore_cost = np.array(site_year_combined['Steel price: Iron Ore ($/tonne)'].values.tolist())
        hydrogen_cost = np.array(site_year_combined['Steel price: Hydrogen ($/tonne)'].values.tolist())# - np.array(site_year_combined['Steel price: Policy savings ($/tonne)'].values.tolist())
        naturalgas_cost = np.array(site_year_combined['Steel price: Natural gas ($/tonne)'].values.tolist())
        electricity_cost = np.array(site_year_combined['Steel price: Electricity ($/tonne)'].values.tolist())
        slagdisposal_cost = np.array(site_year_combined['Steel price: Slag Disposal ($/tonne)'].values.tolist())
        
        other_feedstock_costs = maintmaterials_cost+water_cost+lime_cost+carbon_cost+naturalgas_cost+electricity_cost+slagdisposal_cost
        taxes_cost = np.array(site_year_combined['Steel price: Taxes ($/tonne)'].values.tolist())
        financial_cost = np.array(site_year_combined['Steel price: Equipment Financing ($/tonne)'].values.tolist())+np.array(site_year_combined['Steel price: Remaining Financial ($/tonne)'].values.tolist())
        taxes_financial_costs = taxes_cost+financial_cost
        #policy_savings = np.array(site_year_combined['Steel price: Policy savings ($/tonne)'].values.tolist())
        integration_savings= np.array(site_year_combined['Steel price: Integration Savings ($/tonne)'].values.tolist())

        steel_price_no_policy = np.array(site_year_combined['Steel price: Total ($/tonne)'].values.tolist())
        steel_price_base_policy_savings = np.array(site_year_combined['Steel price: Base policy savings ($/tonne)'].values.tolist())
        steel_price_max_policy_savings = np.array(site_year_combined['Steel price: Max policy savings ($/tonne)'].values.tolist())

        steel_price_base_policy = np.array(site_year_combined['Steel price: Total ($/tonne)'].values.tolist())-np.array(site_year_combined['Steel price: Base policy savings ($/tonne)'].values.tolist())
        steel_price_max_policy = np.array(site_year_combined['Steel price: Total ($/tonne)'].values.tolist())-np.array(site_year_combined['Steel price: Max policy savings ($/tonne)'].values.tolist())

        if atb_year != '2020':
            smr_ngprice_error_low = site_year_smr_sensitivity['LCOS NG price sensitivity low ($/kg)'].values.tolist()
            smr_ngprice_error_high = site_year_smr_sensitivity['LCOS NG price sensitivity high ($/kg)'].values.tolist()

            atr_ngprice_error_low = site_year_atr_sensitivity['LCOS NG price sensitivity low ($/kg)'].values.tolist()
            atr_ngprice_error_high = site_year_atr_sensitivity['LCOS NG price sensitivity high ($/kg)'].values.tolist()

            elec_error_low = (site_year_combined.loc[(site_year_combined['Order']>2)&(site_year_combined['Policy Option']=='no-policy'),'Steel price: Total ($/tonne)'].values-site_year_electrolysis_sensitivity.loc[site_year_electrolysis_sensitivity['Electrolysis cost case']=='EC-cost-Low','Steel price: Total ($/tonne)'].values).tolist()
            elec_error_high = (site_year_electrolysis_sensitivity.loc[site_year_electrolysis_sensitivity['Electrolysis cost case']=='EC-cost-High','Steel price: Total ($/tonne)'].values-site_year_combined.loc[(site_year_combined['Order']>2)&(site_year_combined['Policy Option']=='no-policy'),'Steel price: Total ($/tonne)'].values).tolist()

            error_lcos_low = smr_ngprice_error_low.copy()
            error_lcos_high = smr_ngprice_error_high.copy()

            error_lcos_low.append(atr_ngprice_error_low[0])
            error_lcos_high.append(atr_ngprice_error_high[0])
            for j in range(len(labels)-3):
                []
                error_lcos_low.append(max(0,elec_error_low[j]))
                error_lcos_high.append(max(0,elec_error_high[j]))

        width = 0.5
        #fig, ax = plt.subplots()
        fig, ax = plt.subplots(1,1,figsize=(9,6), dpi= resolution)
        ax.bar(labels,total_cap_cost,width,label='Total CAPEX',edgecolor='dimgray',color='dimgrey')
        barbottom=total_cap_cost
        ax.bar(labels,fixedom_cost,width,bottom=barbottom,label = 'Fixed O&M cost',edgecolor='steelblue',color='deepskyblue')
        barbottom=barbottom+fixedom_cost
        ax.bar(labels,ironore_cost,width,bottom=barbottom,label='Iron Ore',edgecolor='black',color='navy')
        barbottom=barbottom+ironore_cost
        ax.bar(labels,hydrogen_cost,width,bottom=barbottom,label='Hydrogen',edgecolor='cadetblue',color='lightseagreen')
        barbottom=barbottom+hydrogen_cost
        ax.bar(labels,other_feedstock_costs,width,bottom=barbottom,label='Other feedstocks',edgecolor='goldenrod',color='gold')
        barbottom=barbottom+other_feedstock_costs
        ax.bar(labels,taxes_financial_costs,width,bottom=barbottom,label='Taxes and Finances',edgecolor='peru',color='darkorange')
        barbottom=barbottom+taxes_financial_costs
        #ax.bar(labels,policy_savings,width,bottom=barbottom,label='Policy Savings',color='white', edgecolor = 'sandybrown',hatch='.....')
        #barbottom=barbottom+policy_savings
        #ax.bar(labels,integration_savings,width,bottom=barbottom,label = 'Integration Savings',color='white', edgecolor = 'darkgray',hatch='.....')
        #barbottom = barbottom+integration_savings
        #ax.errorbar(labels,barbottom-integration_savings-policy_savings,yerr=[error_low,error_high], fmt='none',elinewidth=[0,0,0,0,0,1],ecolor='none',capsize=6,markeredgewidth=1)  
        #ax.errorbar(labels[5],barbottom[5]-integration_savings[5]-policy_savings[5],yerr=[[error_low[5]],[error_high[5]]],fmt='none',elinewidth=1,capsize=6,markeredgewidth=1,ecolor='black')                                        

        if show_arrows:
            ax.plot([0,1,2,3,4,5], steel_price_base_policy, color='black', marker='o', linestyle='none', markersize=3,label='Base Policy')
            ax.plot([0,1,2,3,4,5], steel_price_max_policy, color='dimgray', marker='s', linestyle='none', markersize=3,label='Max Policy')

        # Plot error bars
        if atb_year != '2020':
            ax.errorbar(labels,steel_price_no_policy,yerr=[error_lcos_low,error_lcos_high], fmt='none',elinewidth=1,ecolor='dimgray',capsize=6,markeredgewidth=1.25)

        arrow_top = np.zeros(len(labels))
        ax.errorbar(labels,steel_price_no_policy,yerr=[arrow_top,arrow_top],fmt='none',elinewidth=1,ecolor='black',capsize=10,markeredgewidth=1.25)
        if show_arrows:
            for j in range(len(labels)):
                ax.arrow(j,barbottom[j],0,-1*steel_price_base_policy_savings[j],head_width=0.1,head_length=35,length_includes_head=True,color='black')
                ax.arrow(j,barbottom[j]-steel_price_base_policy_savings[j],0,-1*(steel_price_max_policy_savings[j]-steel_price_base_policy_savings[j]),head_width=0.1,head_length=35,length_includes_head=True,color='dimgray')

        ax.axhline(y=barbottom[0], color='k', linestyle='--',linewidth=1.5)

        # error_high = np.zeros(len(labels))
        # ax.errorbar(labels,lcoh_withpolicy,yerr=[error_high,error_high], fmt='none',elinewidth=1,ecolor='black',capsize=10,markeredgewidth=1.25) 
        # for j in range(len(labels)): 
        #     ax.arrow(j,lcoh_withpolicy[j],0,-1*lcoh_policy_savings[j],head_width=0.1,head_length=0.4,length_includes_head=True,color='black')
        #     ax.arrow(j,barbottom[j],0,-1*policy_savings[j],head_width=0.1,head_length=0.4,length_includes_head=True,color='black')
        # ax.axhline(y=0, color='k', linestyle='-',linewidth=1.5)
        # ax.axhline(y=lcoh_withpolicy[0], color='k', linestyle='--',linewidth=1.5)
        # barbottom = lcoh_withpolicy


        # Decorations
        ax.set_title(scenario_title, fontsize=title_size)
        ax.spines[['left','top','right','bottom']].set_linewidth(1.5)
        ax.set_ylabel('Breakeven price of steel ($/tonne steel)', fontname = font, fontsize = axis_label_size)
        #ax.set_xlabel('Scenario', fontname = font, fontsize = axis_label_size)
        ax.legend(fontsize = legend_size, ncol = 2, prop = {'family':'Arial','size':legend_size},loc='upper left')
        max_y = np.max(barbottom)
        ax.set_ylim([0,2000])
        #ax.set_ylim([0,1.4*max_y])
        ax.tick_params(axis = 'y',labelsize = tickfontsize,direction = 'in',width=1.5)
        ax.tick_params(axis = 'x',labelsize = tickfontsize,direction = 'in',width=1.5,rotation=45)
        #ax2 = ax.twinx()
        #ax2.set_ylim([0,10])
        #plt.xlim(x[0], x[-1])
        plt.tight_layout()
        plt.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'steelprice_barchart_'+file_name + '_'+retail_string+'_alltechnologies.png',pad_inches = 0.1)
        plt.close(fig = None)
        
        # # Plot ammonia cost breakdown
        # error_low = []
        # error_high = []
        # for j in range(len(labels)-1):
        #     error_low.append(0)
        #     error_high.append(0)
        # error_low.append(max(0,ammonia_error_low))
        # error_high.append(0)
        

        # error_high = np.array(error_high)
        # error_low = np.array(error_low)

        airsep_cap_cost = np.array(site_year_combined['Ammonia price: Air Separation by Cryogenic ($/kg)'].values.tolist())
        haber_bosch_cap_cost = np.array(site_year_combined['Ammonia price: Haber Bosch ($/kg)'].values.tolist())
        boiler_steamturbine_cap_cost = np.array(site_year_combined['Ammonia price: Boiler and Steam Turbine ($/kg)'].values.tolist())
        cooling_tower_cap_cost = np.array(site_year_combined['Ammonia price: Cooling Tower ($/kg)'].values.tolist())
        depreciable_nonequipment_cost = np.array(site_year_combined['Ammonia price: Depreciable Nonequipment ($/kg)'].values.tolist())
        total_cap_cost_ammonia = airsep_cap_cost+haber_bosch_cap_cost+boiler_steamturbine_cap_cost+cooling_tower_cap_cost+depreciable_nonequipment_cost
        
        labor_cost = np.array(site_year_combined['Ammonia price: Labor Cost ($/kg)'].values.tolist())
        maintenance_cost = np.array(site_year_combined['Ammonia price: Maintenance Cost ($/kg)'].values.tolist())
        adminexpense_cost = np.array(site_year_combined['Ammonia price: Administrative Expense ($/kg)'].values.tolist())
        total_fixed_cost_ammonia = labor_cost+maintenance_cost+adminexpense_cost
        
        #policy_savings_ammonia = np.array(site_year_combined['Ammonia price: Policy savings ($/kg)'].values.tolist())
        
        hydrogen_cost = np.array(site_year_combined['Ammonia price: Hydrogen ($/kg)'].values.tolist())# - policy_savings_ammonia
        electricity_cost = np.array(site_year_combined['Ammonia price: Electricity ($/kg)'].values.tolist())
        coolingwater_cost = np.array(site_year_combined['Ammonia price: Cooling water ($/kg)'].values.tolist())
        ironbasedcatalyst_cost = np.array(site_year_combined['Ammonia price: Iron based catalyst ($/kg)'].values.tolist())
        other_feedstock_costs_ammonia = electricity_cost+coolingwater_cost+ironbasedcatalyst_cost
        
        oxygenbyproduct_revenue = -1*np.array(site_year_combined['Ammonia price: Oxygen byproduct ($/kg)'].values.tolist())
        
        taxes_cost = np.array(site_year_combined['Ammonia price: Taxes ($/kg)'].values.tolist())
        financial_cost = np.array(site_year_combined['Ammonia price: Equipment Financing ($/kg)'].values.tolist()) + np.array(site_year_combined['Ammonia price: Remaining Financial ($/kg)'].values.tolist())

        taxes_financial_costs_ammonia = taxes_cost+financial_cost

        ammonia_price_no_policy = np.array(site_year_combined['Ammonia price: Total ($/kg)'].values.tolist())
        ammonia_price_base_policy_savings = np.array(site_year_combined['Ammonia price: Base policy savings ($/kg)'].values.tolist())
        ammonia_price_max_policy_savings = np.array(site_year_combined['Ammonia price: Max policy savings ($/kg)'].values.tolist())
        ammonia_price_base_policy = np.array(site_year_combined['Ammonia price: Total ($/kg)'].values.tolist())- np.array(site_year_combined['Ammonia price: Base policy savings ($/kg)'].values.tolist())
        ammonia_price_max_policy = np.array(site_year_combined['Ammonia price: Total ($/kg)'].values.tolist())- np.array(site_year_combined['Ammonia price: Max policy savings ($/kg)'].values.tolist())


        if atb_year != '2020':
            smr_ngprice_error_low = site_year_smr_sensitivity['LCOA NG price sensitivity low ($/kg)'].values.tolist()
            smr_ngprice_error_high = site_year_smr_sensitivity['LCOA NG price sensitivity high ($/kg)'].values.tolist()

            atr_ngprice_error_low = site_year_atr_sensitivity['LCOA NG price sensitivity low ($/kg)'].values.tolist()
            atr_ngprice_error_high = site_year_atr_sensitivity['LCOA NG price sensitivity high ($/kg)'].values.tolist()

            elec_error_low = (site_year_combined.loc[(site_year_combined['Order']>2)&(site_year_combined['Policy Option']=='no-policy'),'Ammonia price: Total ($/kg)'].values-site_year_electrolysis_sensitivity.loc[site_year_electrolysis_sensitivity['Electrolysis cost case']=='EC-cost-Low','Ammonia price: Total ($/kg)'].values).tolist()
            elec_error_high = (site_year_electrolysis_sensitivity.loc[site_year_electrolysis_sensitivity['Electrolysis cost case']=='EC-cost-High','Ammonia price: Total ($/kg)'].values-site_year_combined.loc[(site_year_combined['Order']>2)&(site_year_combined['Policy Option']=='no-policy'),'Ammonia price: Total ($/kg)'].values).tolist()

            error_lcoa_low = smr_ngprice_error_low.copy()
            error_lcoa_high = smr_ngprice_error_high.copy()

            error_lcoa_low.append(atr_ngprice_error_low[0])
            error_lcoa_high.append(atr_ngprice_error_high[0])
            for j in range(len(labels)-3):
                []
                error_lcoa_low.append(max(0,elec_error_low[j]))
                error_lcoa_high.append(max(0,elec_error_high[j]))

        width = 0.5
        #fig, ax = plt.subplots()
        fig, ax = plt.subplots(1,1,figsize=(9,6), dpi= resolution)
#        ax.bar(labels,oxygenbyproduct_revenue,width,label='Oxygen byproduct revenue')
        ax.bar(labels,total_cap_cost_ammonia,width,label='Total CAPEX',edgecolor='dimgray',color='dimgrey')
        barbottom=total_cap_cost_ammonia
        ax.bar(labels,total_fixed_cost_ammonia,width,bottom=barbottom,label = 'Fixed O&M cost',edgecolor='steelblue',color='deepskyblue')
        barbottom=barbottom+total_fixed_cost_ammonia
        ax.bar(labels,hydrogen_cost,width,bottom=barbottom,label='Hydrogen',edgecolor='cadetblue',color='lightseagreen')
        barbottom=barbottom+hydrogen_cost
        ax.bar(labels,other_feedstock_costs_ammonia,width,bottom=barbottom,label='Other feedstocks',edgecolor='goldenrod',color='gold')
        barbottom=barbottom+other_feedstock_costs_ammonia
        ax.bar(labels,taxes_financial_costs_ammonia,width,bottom=barbottom,label='Taxes and Finances',edgecolor='peru',color='darkorange')
        barbottom = barbottom+taxes_financial_costs_ammonia
        #ax.bar(labels,policy_savings_ammonia,width,bottom=barbottom,label = 'Policy Savings',color='white', edgecolor = 'sandybrown',hatch='.....')
        #barbottom=barbottom+policy_savings_ammonia

        if show_arrows:
            ax.plot([0,1,2,3,4,5], ammonia_price_base_policy, color='black', marker='o', linestyle='none', markersize=3,label='Base Policy')
            ax.plot([0,1,2,3,4,5], ammonia_price_max_policy, color='dimgray', marker='s', linestyle='none', markersize=3,label='Max Policy')

        # Plot NG error bars
        if atb_year != '2020':
            ax.errorbar(labels,ammonia_price_no_policy,yerr=[error_lcoa_low,error_lcoa_high], fmt='none',elinewidth=1,ecolor='dimgray',capsize=6,markeredgewidth=1.25)

        arrow_top = np.zeros(len(labels))
        ax.errorbar(labels,barbottom,yerr=[arrow_top,arrow_top],fmt='none',elinewidth=1,ecolor='black',capsize=10,markeredgewidth=1.25)
        if show_arrows:
            for j in range(len(labels)):
                ax.arrow(j,barbottom[j],0,-1*ammonia_price_base_policy_savings[j],head_width=0.1,head_length=0.08,length_includes_head=True,color='black')
                ax.arrow(j,barbottom[j]-ammonia_price_base_policy_savings[j],0,-1*(ammonia_price_max_policy_savings[j]-ammonia_price_base_policy_savings[j]),head_width=0.1,head_length=0.08,length_includes_head=True,color='dimgray')
        #ax.errorbar(labels,barbottom-policy_savings_ammonia,yerr=[error_low,error_high], fmt='none',elinewidth=[0,0,0,0,0,1],ecolor='none',capsize=6,markeredgewidth=1)                                        
        #ax.errorbar(labels[5],barbottom[5]-policy_savings_ammonia[5],yerr=[[error_low[5]],[error_high[5]]],fmt='none',elinewidth=1,capsize=6,markeredgewidth=1,ecolor='black')                                        
        ax.axhline(y=0.0, color='k', linestyle='-',linewidth=1.5)
        ax.axhline(y=barbottom[0], color='k', linestyle='--',linewidth=1.5)

        
        # Decorations
        ax.set_title(scenario_title, fontsize=title_size)
        ax.spines[['left','top','right','bottom']].set_linewidth(1.5)
        ax.set_ylabel('Breakeven price of ammonia ($/kg-NH3)', fontname = font, fontsize = axis_label_size)
        ax.legend(fontsize = legend_size, ncol = 2, prop = {'family':'Arial','size':legend_size},loc='upper left')
        min_y = np.min(oxygenbyproduct_revenue)
        max_y = np.max(barbottom+taxes_financial_costs_ammonia)
        #ax.set_ylim([-0.25,1.4*max_y])
        ax.set_ylim([-0.5,4.0])
        ax.tick_params(axis = 'y',labelsize = tickfontsize,direction = 'in',width=1.5)
        ax.tick_params(axis = 'x',labelsize = tickfontsize,direction = 'in',width=1.5,rotation = 45)
        plt.tight_layout()
        plt.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'ammoniaprice_barchart_'+file_name + '_'+retail_string+'_alltechnologies.png',pad_inches = 0.1)
        plt.close(fig = None)

        print('Done!')