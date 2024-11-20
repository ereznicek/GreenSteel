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

#Read in LCA results
lca_summary = pd.read_csv('Results_LCA/LCA_results.csv',index_col=0,header = 0)

# Directories
plot_directory = 'Plots'
plot_subdirectory = 'LCA_stacked_plots_alltech_alllocations_allyears'

retail_string = 'retail-flat'

# Narrow down to retail price of interest
if retail_string == 'retail-flat':
    lca_summary = lca_summary.loc[(lca_summary['Grid case']!='grid-only-wholesale') & (lca_summary['Grid case']!='hybrid-grid-wholesale')]
elif retail_string == 'wholesale':
    lca_summary = lca_summary.loc[(lca_summary['Grid Case']!='grid-only-retail-flat') & (lca_summary['Grid Case']!='hybrid-grid-retail-flat')]

# Add labels for plotting
lca_summary.loc[lca_summary['Grid case']=='grid-only-'+retail_string,'Label']='Grid Only'
lca_summary.loc[lca_summary['Grid case']=='grid-only-'+retail_string,'Order']= 3
#lca_summary.loc[(lca_summary['Grid case']=='hybrid-grid-'+retail_string) & (lca_summary['Renewables case']=='Wind'),'Label']='Grid + Wind'
#lca_summary.loc[(lca_summary['Grid case']=='hybrid-grid-'+retail_string) & (lca_summary['Renewables case']=='Wind'),'Order']=3
lca_summary.loc[(lca_summary['Grid case']=='hybrid-grid-'+retail_string) & (lca_summary['Renewables case']=='Wind+PV+bat'),'Label']='Grid + Wind + PV'
lca_summary.loc[(lca_summary['Grid case']=='hybrid-grid-'+retail_string) & (lca_summary['Renewables case']=='Wind+PV+bat'),'Order']=4
#lca_summary.loc[(lca_summary['Grid case']=='off-grid') & (lca_summary['Renewables case']=='Wind') & (lca_summary['Electrolysis case']=='Centralized'),'Label']='Wind, CE'
#lca_summary.loc[(lca_summary['Grid case']=='off-grid') & (lca_summary['Renewables case']=='Wind') & (lca_summary['Electrolysis case']=='Centralized'),'Order']=5
lca_summary.loc[(lca_summary['Grid case']=='off-grid') & (lca_summary['Renewables case']=='Wind+PV+bat') & (lca_summary['Electrolysis case']=='Centralized'),'Label']='Wind + PV + bat'
lca_summary.loc[(lca_summary['Grid case']=='off-grid') & (lca_summary['Renewables case']=='Wind+PV+bat') & (lca_summary['Electrolysis case']=='Centralized'),'Order']=5
#lca_summary.loc[(lca_summary['Grid case']=='off-grid') & (lca_summary['Renewables case']=='Wind') & (lca_summary['Electrolysis case']=='Distributed'),'Label']='Wind, DE'
#lca_summary.loc[(lca_summary['Grid case']=='off-grid') & (lca_summary['Renewables case']=='Wind') & (lca_summary['Electrolysis case']=='Distributed'),'Order']=7
#lca_summary.loc[(lca_summary['Grid case']=='off-grid') & (lca_summary['Renewables case']=='Wind+PV+bat') & (lca_summary['Electrolysis case']=='Distributed'),'Label']='Wind+PV+bat, DE'
#lca_summary.loc[(lca_summary['Grid case']=='off-grid') & (lca_summary['Renewables case']=='Wind+PV+bat') & (lca_summary['Electrolysis case']=='Distributed'),'Order']=8

locations = [
            'IN',
            'TX',
            'IA',
            'MS',
            'MN'
             ]
years = [
    2022,
    2025,
    2030,
    2035
    ]

location_strings = {
                    'IN':'Indiana',
                    'TX':'Texas',
                    'IA':'Iowa',
                    'MS':'Mississippi',
                    'MN':'Minnesota'
                    }

# Global Plot Settings
font = 'Arial'
title_size = 14
axis_label_size = 14
legend_size = 12
tick_size = 14
tickfontsize = 14
resolution = 150

fig,ax=plt.subplots(len(locations),len(years),sharex=True,sharey=True,dpi= resolution)
fig.tight_layout()
fig.set_figwidth(12)
fig.set_figheight(12)       

fig1,ax1=plt.subplots(len(locations),len(years),sharex=True,sharey=True,dpi= resolution)
fig1.tight_layout()
fig1.set_figwidth(12)
fig1.set_figheight(12)  

fig2,ax2=plt.subplots(len(locations),len(years),sharex=True,sharey=True,dpi= resolution)
fig2.tight_layout()
fig2.set_figwidth(12)
fig2.set_figheight(12)  

for axi1,site in enumerate(locations):
    for axi2,atb_year in enumerate(years):
        #site = 'TX'
        #atb_year = '2025'
        
        # Limit to cases for specific site and year
        site_year_lca = lca_summary.loc[(lca_summary['Site']==site) & (lca_summary['Year']==atb_year) & (lca_summary['Policy Option']=='no-policy')]
        # Sort use cases
        site_year_lca = site_year_lca.sort_values(by='Order',ignore_index=True)

        # Set up SMR cases
        hydrogen_scope_1 = [pd.unique(site_year_lca['SMR Scope 1 GHG Emissions (kg-CO2e/kg-H2)'])[0],pd.unique(site_year_lca['SMR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-H2)'])[0]]
        hydrogen_scope_2 = [pd.unique(site_year_lca['SMR Scope 2 GHG Emissions (kg-CO2e/kg-H2)'])[0],pd.unique(site_year_lca['SMR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-H2)'])[0]]
        hydrogen_scope_3 = [pd.unique(site_year_lca['SMR Scope 3 GHG Emissions (kg-CO2e/kg-H2)'])[0],pd.unique(site_year_lca['SMR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-H2)'])[0]]

        steel_scope_1 = [pd.unique(site_year_lca['Steel SMR Scope 1 GHG Emissions (kg-CO2e/MT steel)'])[0],pd.unique(site_year_lca['Steel SMR with CCS Scope 1 GHG Emissions (kg-CO2e/MT steel)'])[0]]
        steel_scope_2 = [pd.unique(site_year_lca['Steel SMR Scope 2 GHG Emissions (kg-CO2e/MT steel)'])[0],pd.unique(site_year_lca['Steel SMR with CCS Scope 2 GHG Emissions (kg-CO2e/MT steel)'])[0]]
        steel_scope_3 = [pd.unique(site_year_lca['Steel SMR Scope 3 GHG Emissions (kg-CO2e/MT steel)'])[0],pd.unique(site_year_lca['Steel SMR with CCS Scope 3 GHG Emissions (kg-CO2e/MT steel)'])[0]]

        ammonia_scope_1 = [pd.unique(site_year_lca['Ammonia SMR Scope 1 GHG Emissions (kg-CO2e/kg-NH3)'])[0],pd.unique(site_year_lca['Ammonia SMR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-NH3)'])[0]]
        ammonia_scope_2 = [pd.unique(site_year_lca['Ammonia SMR Scope 2 GHG Emissions (kg-CO2e/kg-NH3)'])[0],pd.unique(site_year_lca['Ammonia SMR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-NH3)'])[0]]
        ammonia_scope_3 = [pd.unique(site_year_lca['Ammonia SMR Scope 3 GHG Emissions (kg-CO2e/kg-NH3)'])[0],pd.unique(site_year_lca['Ammonia SMR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-NH3)'])[0]]

        #Set up ATR cases
        hydrogen_scope_1.append(pd.unique(site_year_lca['ATR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-H2)'])[0])
        hydrogen_scope_2.append(pd.unique(site_year_lca['ATR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-H2)'])[0])
        hydrogen_scope_3.append(pd.unique(site_year_lca['ATR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-H2)'])[0])

        steel_scope_1.append(pd.unique(site_year_lca['Steel ATR with CCS Scope 1 GHG Emissions (kg-CO2e/MT steel)'])[0])
        steel_scope_2.append(pd.unique(site_year_lca['Steel ATR with CCS Scope 2 GHG Emissions (kg-CO2e/MT steel)'])[0])
        steel_scope_3.append(pd.unique(site_year_lca['Steel ATR with CCS Scope 3 GHG Emissions (kg-CO2e/MT steel)'])[0])

        ammonia_scope_1.append(pd.unique(site_year_lca['Ammonia ATR with CCS Scope 1 GHG Emissions (kg-CO2e/kg-NH3)'])[0])
        ammonia_scope_2.append(pd.unique(site_year_lca['Ammonia ATR with CCS Scope 2 GHG Emissions (kg-CO2e/kg-NH3)'])[0])
        ammonia_scope_3.append(pd.unique(site_year_lca['Ammonia ATR with CCS Scope 3 GHG Emissions (kg-CO2e/kg-NH3)'])[0])

        # Set up electrolysis cases
        hydrogen_electrolysis_scope_1 = np.array(site_year_lca['Electrolysis Scope 1 GHG Emissions (kg-CO2e/kg-H2)'].values.tolist())
        hydrogen_electrolysis_scope_2 = np.array(site_year_lca['Electrolysis Scope 2 GHG Emissions (kg-CO2e/kg-H2)'].values.tolist())
        hydrogen_electrolysis_scope_3 = np.array(site_year_lca['Electrolysis Scope 3 GHG Emissions (kg-CO2e/kg-H2)'].values.tolist())

        steel_electrolysis_scope_1 = np.array(site_year_lca['Steel Electrolysis Scope 1 GHG Emissions (kg-CO2e/MT steel)'].values.tolist())
        steel_electrolysis_scope_2 = np.array(site_year_lca['Steel Electrolysis Scope 2 GHG Emissions (kg-CO2e/MT steel)'].values.tolist())
        steel_electrolysis_scope_3 = np.array(site_year_lca['Steel Electrolysis Scope 3 GHG Emissions (kg-CO2e/MT steel)'].values.tolist())

        ammonia_electrolysis_scope_1 = np.array(site_year_lca['Ammonia Electrolysis Scope 1 GHG Emissions (kg-CO2e/kg-NH3)'].values.tolist())
        ammonia_electrolysis_scope_2 = np.array(site_year_lca['Ammonia Electrolysis Scope 2 GHG Emissions (kg-CO2e/kg-NH3)'].values.tolist())
        ammonia_electrolysis_scope_3 = np.array(site_year_lca['Ammonia Electrolysis Scope 3 GHG Emissions (kg-CO2e/kg-NH3)'].values.tolist())

        labels = ['SMR','SMR + CCS','ATR + CCS']

        # Combine SMR and electrolysis cases
        for j in range(len(hydrogen_electrolysis_scope_1)):
            hydrogen_scope_1.append(hydrogen_electrolysis_scope_1[j])
            hydrogen_scope_2.append(hydrogen_electrolysis_scope_2[j])
            hydrogen_scope_3.append(hydrogen_electrolysis_scope_3[j])

            steel_scope_1.append(steel_electrolysis_scope_1[j])
            steel_scope_2.append(steel_electrolysis_scope_2[j])
            steel_scope_3.append(steel_electrolysis_scope_3[j])

            ammonia_scope_1.append(ammonia_electrolysis_scope_1[j])
            ammonia_scope_2.append(ammonia_electrolysis_scope_2[j])
            ammonia_scope_3.append(ammonia_electrolysis_scope_3[j])

            labels.append(site_year_lca['Label'].values.tolist()[j])

        # convert to arrays for plotting
        hydrogen_scope_1 = np.array(hydrogen_scope_1)
        hydrogen_scope_2 = np.array(hydrogen_scope_2)
        hydrogen_scope_3 = np.array(hydrogen_scope_3)

        steel_scope_1 = np.array(steel_scope_1)
        steel_scope_2 = np.array(steel_scope_2)
        steel_scope_3 = np.array(steel_scope_3)

        ammonia_scope_1 = np.array(ammonia_scope_1)
        ammonia_scope_2 = np.array(ammonia_scope_2)
        ammonia_scope_3 = np.array(ammonia_scope_3)

        width = 0.5
        # Plot hydrogen emissions
        ax[axi1,axi2].bar(labels,hydrogen_scope_1,label='GHG Scope 1 Emissions',edgecolor='steelblue',color='deepskyblue')
        barbottom=hydrogen_scope_1
        ax[axi1,axi2].bar(labels,hydrogen_scope_2,bottom=barbottom,label = 'GHG Scope 2 Emissions',edgecolor='dimgray',color='dimgrey')
        barbottom = barbottom+hydrogen_scope_2
        ax[axi1,axi2].bar(labels,hydrogen_scope_3,bottom=barbottom,label = 'GHG Scope 3 Emissions',edgecolor='black',color = 'navy')
        barbottom=barbottom+hydrogen_scope_3

        #Plot column title
        if atb_year == 2022:
            plot_title = 'Current'
        else:
            plot_title = str(atb_year)

        # Decorations
        if axi1==0:
            ax[axi1,axi2].set_title(plot_title,fontsize=title_size)
        ax[axi1,axi2].spines[['left','top','right','bottom']].set_linewidth(1.5)
        if axi2==0:
            ax[axi1,axi2].set_ylabel(location_strings[site] + '\n H2 Emissions \n (kg-CO2/kg-H2)', fontname = font, fontsize = axis_label_size)
        ax[axi1,axi2].tick_params(axis = 'y',labelsize = tickfontsize,direction = 'in',width=1.5)
        ax[axi1,axi2].tick_params(axis = 'x',labelsize = tickfontsize,direction = 'in',width=1.5,rotation=90)
        h2_handles,h2_labels = ax[axi1,axi2].get_legend_handles_labels()

        # Plot steel emissions
        ax1[axi1,axi2].bar(labels,steel_scope_1,label='GHG Scope 1 Emissions',edgecolor='steelblue',color='deepskyblue')
        barbottom=steel_scope_1
        ax1[axi1,axi2].bar(labels,steel_scope_2,bottom=barbottom,label = 'GHG Scope 2 Emissions',edgecolor='dimgray',color='dimgrey')
        barbottom = barbottom+steel_scope_2
        ax1[axi1,axi2].bar(labels,steel_scope_3,bottom=barbottom,label = 'GHG Scope 3 Emissions',edgecolor='black',color = 'navy')
        barbottom=barbottom+steel_scope_3

        # Decorations
        if axi1==0:
            ax1[axi1,axi2].set_title(plot_title,fontsize=title_size)
        ax1[axi1,axi2].spines[['left','top','right','bottom']].set_linewidth(1.5)
        if axi2==0:
            ax1[axi1,axi2].set_ylabel(location_strings[site] + '\n Steel Emissions \n (kg-CO2/tonne-steel)', fontname = font, fontsize = axis_label_size)
        ax1[axi1,axi2].tick_params(axis = 'y',labelsize = tickfontsize,direction = 'in',width=1.5)
        ax1[axi1,axi2].tick_params(axis = 'x',labelsize = tickfontsize,direction = 'in',width=1.5,rotation=90)
        steel_handles,steel_labels = ax1[axi1,axi2].get_legend_handles_labels()

        # Plot ammonia emissions
        ax2[axi1,axi2].bar(labels,ammonia_scope_1,label='GHG Scope 1 Emissions',edgecolor='steelblue',color='deepskyblue')
        barbottom=ammonia_scope_1
        ax2[axi1,axi2].bar(labels,ammonia_scope_2,bottom=barbottom,label = 'GHG Scope 2 Emissions',edgecolor='dimgray',color='dimgrey')
        barbottom = barbottom+ammonia_scope_2
        ax2[axi1,axi2].bar(labels,ammonia_scope_3,bottom=barbottom,label = 'GHG Scope 3 Emissions',edgecolor='black',color = 'navy')
        barbottom=barbottom+ammonia_scope_3

        # Decorations
        if axi1==0:
            ax2[axi1,axi2].set_title(plot_title,fontsize=title_size)
        ax2[axi1,axi2].spines[['left','top','right','bottom']].set_linewidth(1.5)
        if axi2==0:
            ax2[axi1,axi2].set_ylabel(location_strings[site] + '\n Ammonia Emissions \n (kg-CO2/kg-NH3)', fontname = font, fontsize = axis_label_size)
        ax2[axi1,axi2].tick_params(axis = 'y',labelsize = tickfontsize,direction = 'in',width=1.5)
        ax2[axi1,axi2].tick_params(axis = 'x',labelsize = tickfontsize,direction = 'in',width=1.5,rotation=90)
        ammonia_handles,ammonia_labels = ax2[axi1,axi2].get_legend_handles_labels()

fig.legend(h2_handles,h2_labels,fontsize = legend_size, ncol = 3, prop = {'family':'Arial','size':legend_size},loc='upper center',bbox_to_anchor=(0.5,0))
fig.tight_layout()
fig.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'lca_barchart_hydrogen_' +retail_string+'_alltechnologies_alllocations_allyears.png',pad_inches = 0.1,bbox_inches='tight')

fig1.legend(steel_handles,steel_labels,fontsize = legend_size, ncol = 3, prop = {'family':'Arial','size':legend_size},loc='upper center',bbox_to_anchor=(0.5,0))
fig1.tight_layout()
fig1.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'lca_barchart_steel_' +retail_string+'_alltechnologies_alllocations_allyears.png',pad_inches = 0.1,bbox_inches='tight')

fig2.legend(ammonia_handles,ammonia_labels,fontsize = legend_size, ncol = 3, prop = {'family':'Arial','size':legend_size},loc='upper center',bbox_to_anchor=(0.5,0))
fig2.tight_layout()
fig2.savefig(plot_directory +'/' + plot_subdirectory +'/' + 'lca_barchart_ammonia_' +retail_string+'_alltechnologies_alllocations_allyears.png',pad_inches = 0.1,bbox_inches='tight')

[]
