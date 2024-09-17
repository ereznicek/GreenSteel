import os
import sys
sys.path.append('')
from dotenv import load_dotenv
import pandas as pd
from scipy.spatial.distance import cdist
from hopp.utilities.keys import set_developer_nrel_gov_key
# from plot_reopt_results import plot_reopt_results
# from run_reopt import run_reopt
from hopp.to_organize.H2_Analysis.hopp_for_h2 import hopp_for_h2
from hopp.to_organize.H2_Analysis.run_h2a import run_h2a as run_h2a
from hopp.to_organize.H2_Analysis.simple_cash_annuals import simple_cash_annuals

import numpy as np
from lcoe.lcoe import lcoe as lcoe_calc
import warnings
warnings.filterwarnings("ignore")

#import hopp.to_organize.hopp_tools_steel as hopp_tools_steel
import hopp_tools_steel
import copy
#import hopp.to_organize.run_profast_for_hydrogen as run_profast_for_hydrogen
import run_profast_for_hydrogen
#import hopp.to_organize.distributed_pipe_cost_analysis
import distributed_pipe_cost_analysis
from grid_price_profiles import grid_price_interpolation
#import hopp_tools_run_wind_solar
#from hybrid.PEM_Model_2Push import run_PEM_master

def solar_storage_param_sweep(project_path,arg_list,save_best_solar_case_pickle,save_param_sweep_summary,solar_test_sizes_mw_AC=None,battery_sizes_mw=None,battery_sizes_mwh=None):

    # Read in arguments
    # [policy, i, atb_year, site_location, electrolysis_scale,run_RODeO_selector,floris,\
    #  grid_connection_scenario,grid_price_scenario,\
    #  direct_coupling,steel_annual_production_rate_target_tpy,parent_path,results_dir,fin_sum_dir,rodeo_output_dir,floris_dir,path,\
    #  save_hybrid_plant_yaml,save_model_input_yaml,save_model_output_yaml,number_pem_stacks] = arg_list


    from hopp.simulation.technologies.sites import flatirons_site as sample_site # For some reason we have to pull this inside the definition


    """
    Perform a LCOH analysis for an offshore wind + Hydrogen PEM system

    Missing Functionality:
    1. Figure out H2A Costs or ammortize cost/kw electrolyzer figure and add opex

    ~1. Offshore wind site locations and cost details (4 sites, $1300/kw capex + BOS cost which will come from Orbit Runs)~

    2. Cost Scaling Based on Year (Have Weiser et. al report with cost scaling for fixed and floating tech, will implement)
    3. Cost Scaling Based on Plant Size (Shields et. Al report)
    4. Integration Required:
    * Pressure Vessel Model~
    * HVDC Model
    * Pipeline Model

    5. Model Development Required:
    - Floating Electrolyzer Platform
    """
    [atb_year, policy_option,policy,hopp_dict_init,
     electrolysis_scale,scenario,\
     parent_path,results_dir,\
     grid_connected_hopp,grid_connection_scenario, grid_price_scenario,\
     site_df,sample_site,site,site_location,\
     turbine_model,wind_size_mw,nTurbs,floris_config,floris,\
     sell_price,buy_price,discount_rate,debt_equity_split,\
     electrolyzer_size_mw,electrolyzer_capacity_EOL_MW,n_pem_clusters,pem_control_type,hydrogen_demand_kgphr,
     electrolyzer_capex_kw,electrolyzer_component_costs_kw,wind_plant_degradation_power_decrease,electrolyzer_energy_kWh_per_kg, time_between_replacement,
     user_defined_stack_replacement_time,use_optimistic_pem_efficiency,electrolyzer_degradation_penalty,storage_capacity_multiplier,hydrogen_production_capacity_required_kgphr,\
     electrolyzer_model_parameters,electricity_production_target_MWhpyr,turbine_rating,electrolyzer_degradation_power_increase,cluster_cap_mw,interconnection_size_mw,solar_ITC,grid_price_filename,
     gams_locations_rodeo_version,rodeo_output_dir,run_RODeO_selector,hydrogen_production_target_kgpy] = arg_list

    electrolyzer_installation_factor = 12/100
    electrolyzer_direct_cost_kw = electrolyzer_capex_kw*(1+electrolyzer_installation_factor)

    #Set API key
    hopp_dict=copy.copy(hopp_dict_init)
    load_dotenv()
    NREL_API_KEY = os.getenv("NREL_API_KEY")
    set_developer_nrel_gov_key('NREL_API_KEY')

    useful_life=scenario['Useful Life']

    # user_defined_electrolyzer_EOL_eff_drop = False
    # EOL_eff_drop = []
    # user_defined_electrolyzer_BOL_kWh_per_kg = False
    # BOL_kWh_per_kg = []
    # electrolyzer_model_parameters ={
    # 'Modify BOL Eff':user_defined_electrolyzer_BOL_kWh_per_kg,
    # 'BOL Eff [kWh/kg-H2]':BOL_kWh_per_kg,
    # 'Modify EOL Degradation Value':user_defined_electrolyzer_EOL_eff_drop,
    # 'EOL Rated Efficiency Drop':EOL_eff_drop}
    if solar_test_sizes_mw_AC is None:
        solar_sizes_mw_AC=[0,50,100,250,500,750]
    else:
        solar_sizes_mw_AC=solar_test_sizes_mw_AC
    if battery_sizes_mw is None:
        storage_sizes_mw_temp=[0,50,100,200]
    else:
        storage_sizes_mw=battery_sizes_mw
        storage_sizes_mw_temp=battery_sizes_mw

    if battery_sizes_mwh is None:
        nonzero_storage_sizes=[bmw for bmw in storage_sizes_mw_temp if bmw>0]
        storage_sizes_mwh = list(1*np.array(nonzero_storage_sizes)) + list(2*np.array(nonzero_storage_sizes)) + list(4*np.array(nonzero_storage_sizes))
        storage_sizes_mw=[0]+storage_sizes_mw_temp*3
    else:
        storage_sizes_mwh=battery_sizes_mwh
    battery_for_minimum_electrolyzer_op=True #If true, then dispatch battery (if on) to supply minimum power for operation to PEM, otherwise use it for rated PEM power
    kw_continuous = electrolyzer_size_mw * 1000
    load = [kw_continuous for x in
            range(0, 8760)]  # * (sin(x) + pi) Set desired/required load profile for plant
    if battery_for_minimum_electrolyzer_op:
        battery_dispatch_load = list(0.15*np.array(load))
    else:
        battery_dispatch_load = list(np.array(load))

    st_xl=pd.read_csv(parent_path + '/H2_Analysis/storage_costs_ATB.csv',index_col=0)
    storage_costs=st_xl[str(atb_year)]
    storage_cost_main_kwh=storage_costs['Battery Energy Capital Cost ($/kWh)']
    storage_cost_main_kw=storage_costs['Battery Power Capital Cost ($/kW)']
    storage_om_percent = 0.025 #percent of capex
    renewable_plant_cost = {}

    # Flags (TODO: remove them and update documentation)
    forced_sizes = True
    plot_grid = False

    site_name = site_df['State']

    total_capex = site_df['{} CapEx'.format(atb_year)]
    wind_om_cost_kw = site_df['{} OpEx ($/kw-yr)'.format(atb_year)]*(1+wind_plant_degradation_power_decrease)
    capex_multiplier = site_df['CapEx Multiplier']
    wind_cost_kw = copy.deepcopy(total_capex) * capex_multiplier*(1+wind_plant_degradation_power_decrease)
    hopp_dict.main_dict['Configuration']['wind_om_cost_kw']=wind_om_cost_kw
    hopp_dict.main_dict['Configuration']['wind_cost_kw']=wind_cost_kw

    solar_main_om_cost_kw=site_df[str(atb_year) + ' PV OpEx']
    solar_capex_multiplier=site_df['PV Capex Multiplier']
    solar_capex=site_df[str(atb_year) + ' PV base installed cost']
    solar_main_cost_kw=solar_capex * solar_capex_multiplier

    # solar_cost_kw = copy.copy(solar_main_cost_kw)
    # solar_om_cost_kw = copy.copy(solar_main_om_cost_kw)

    # if storage_size_mw>0:
    #     #battery_desc='{}MW_{}Hr_Battery'
    #     storage_size_mwh = storage_sizes_mwh[bi]
    #     storage_hours = storage_size_mwh/storage_size_mw
    #     battery_desc='{}MW_{}Hr_Battery'.format(storage_size_mw,round(storage_hours))
    #     storage_cost_kw=copy.copy(storage_cost_main_kw)
    #     storage_cost_kwh=copy.copy(storage_cost_main_kwh)
    # else:
    #     battery_desc='NoBattery'
    #     storage_size_mwh =0
    #     storage_cost_kw=0
    #     storage_cost_kwh=0
    #     storage_hours= 0

    # # Estimate capacity factor of solar PV and wind
    # wind_size_mw_test = wind_size_mw
    # solar_size_mw_test = 500
    # storage_size_mw_test = 0
    # storage_size_mwh_test = 0
    # run_wind_plant=True

    # Run HOPP
    # hopp_dict_test, plant_power_production_test, plant_shortfall_hopp_test, plant_curtailment_hopp_test, hybrid_plant_test, wind_size_mw_test, solar_size_mw_test, lcoe_test = \
    #     hopp_tools_steel.run_HOPP(
    #                 project_path,
    #                 hopp_dict,
    #                 scenario,
    #                 site,
    #                 sample_site,
    #                 forced_sizes,
    #                 solar_size_mw_test,
    #                 wind_size_mw_test,
    #                 storage_size_mw_test,
    #                 storage_size_mwh_test,
    #                 wind_cost_kw,
    #                 solar_cost_kw,
    #                 storage_cost_kw,
    #                 storage_cost_kwh,
    #                 kw_continuous,
    #                 load,
    #                 electrolyzer_size_mw,
    #                 wind_om_cost_kw,
    #                 solar_om_cost_kw,
    #                 nTurbs,
    #                 floris_config,
    #                 floris,
    #                 run_wind_plant
    #             )

    lcoh_tracker=[]
    min_lcoh=1000000
    solar_case_tracker=[]
    solar_size_tracker=[]
    battery_chargeRate_tracker=[]
    battery_hour_tracker=[]
    battery_case_tracker=[]
    h2_transmission_price_tracker=[]
    elec_cf_tracker=[]
    plant_cf_tracker=[]
    best_result_data={}
    print('Running solar and battery parameter sweep with {} solar sizes and {} battery sizes...'.format(len(solar_sizes_mw_AC),len(battery_sizes_mw)))
    #start=time.perf_counter()
    for si,solar_size_mw_AC in enumerate(solar_sizes_mw_AC):
        solar_desc='{}MW_Solar'.format(solar_size_mw_AC)
        #print(solar_desc)
        renewable_plant_cost['wind']={'o&m_per_kw':wind_om_cost_kw,'capex_per_kw':wind_cost_kw,'size_mw':wind_size_mw}

        if solar_size_mw_AC>0:
            solar_cost_kw_AC = copy.copy(solar_main_cost_kw)
            solar_om_cost_kw_AC = copy.copy(solar_main_om_cost_kw)
        else:
            solar_om_cost_kw_AC=0
            solar_cost_kw_AC=0

        solar_DC_AC_ratio = 1.3
        solar_size_mw_DC = solar_size_mw_AC*solar_DC_AC_ratio
        solar_cost_kw_DC = solar_cost_kw_AC/solar_DC_AC_ratio
        solar_om_cost_kw_DC = solar_om_cost_kw_AC/solar_DC_AC_ratio

        hopp_dict.main_dict['Configuration']['solar_size']=solar_size_mw_AC
        hopp_dict.main_dict['Configuration']['solar_cost_kw']=solar_cost_kw_AC
        hopp_dict.main_dict['Configuration']['solar_om_cost_kw']=solar_om_cost_kw_AC
        renewable_plant_cost['pv']={'o&m_per_kw':solar_om_cost_kw_AC,
        'capex_per_kw':solar_cost_kw_AC,
        'size_mw':solar_size_mw_AC}

        for bi,storage_size_mw in enumerate(storage_sizes_mw):
        #     if si==0 and bi==0:
        #         run_wind_plant=True
        #     else:
        #         run_wind_plant=False
            run_wind_plant = True

            if storage_size_mw>0:
                #battery_desc='{}MW_{}Hr_Battery'
                storage_size_mwh = storage_sizes_mwh[bi]
                storage_hours = storage_size_mwh/storage_size_mw
                battery_desc='{}MW_{}Hr_Battery'.format(storage_size_mw,round(storage_hours))
                storage_cost_kw=copy.copy(storage_cost_main_kw)
                storage_cost_kwh=copy.copy(storage_cost_main_kwh)
            else:
                battery_desc='NoBattery'
                storage_size_mwh =0
                storage_cost_kw=0
                storage_cost_kwh=0
                storage_hours= 0
            #print(battery_desc)
            if save_param_sweep_summary:
                solar_case_tracker.append(solar_desc)
                battery_case_tracker.append(battery_desc)
                solar_size_tracker.append(solar_size_mw_AC)
                battery_hour_tracker.append(storage_hours)
                battery_chargeRate_tracker.append(storage_size_mw)


            hopp_dict.main_dict['Configuration']['storage_size_mw']=storage_size_mw
            hopp_dict.main_dict['Configuration']['storage_size_mwh']=storage_size_mwh
            hopp_dict.main_dict['Configuration']['battery_cost_kw']=storage_cost_kw
            hopp_dict.main_dict['Configuration']['battery_cost_kwh']=storage_cost_kwh
            # hopp_dict['Configuration']['battery_om_percent'] = storage_om_percent
            renewable_plant_cost['battery']={'capex_per_kw':storage_cost_kw,
            'capex_per_kwh':storage_cost_kwh,
            'o&m_percent':storage_om_percent,
            'size_mw':storage_size_mw,
            'size_mwh':storage_size_mwh,
            'storage_hours':storage_hours}

            # Estimate revised sizing of things
            # Run HOPP
            hopp_dict_cfest, plant_power_production_cfest, plant_shortfall_hopp_cfest, plant_curtailment_hopp_cfest, hybrid_plant_cfest, wind_size_mw_cfest, solar_size_mw_DC_cfest, lcoe_cfest = \
                hopp_tools_steel.run_HOPP(
                            project_path,
                            hopp_dict,
                            scenario,
                            site,
                            sample_site,
                            forced_sizes,
                            solar_size_mw_DC,
                            wind_size_mw,
                            storage_size_mw,
                            storage_size_mwh,
                            wind_cost_kw,
                            solar_cost_kw_DC,
                            storage_cost_kw,
                            storage_cost_kwh,
                            kw_continuous,
                            load,
                            electrolyzer_size_mw,
                            wind_om_cost_kw,
                            solar_om_cost_kw_DC,
                            nTurbs,
                            floris_config,
                            floris,
                            run_wind_plant
                        )

            # Get estimates of solar and wind CFs
            if solar_size_mw_AC > 0:
                solar_cf_DC_est = hybrid_plant_cfest.pv.capacity_factor/100
            else:
                solar_cf_DC_est = 0

            solar_cf_AC_est = solar_cf_DC_est*solar_DC_AC_ratio

            # if wind_size_mw > 0:
            #     wind_cf_est = hybrid_plant_cfest.wind.capacity_factor/100
            # else:
            #     wind_cf_est = 0
            if wind_size_mw > 0:
                wind_power_norm = np.array(hybrid_plant_cfest.wind.generation_profile[:8760])/(wind_size_mw*1000)
            else:
                wind_power_norm = np.zeros(8760)
            if solar_size_mw_AC > 0:
                solar_power_norm_AC = np.array(hybrid_plant_cfest.pv.generation_profile[:8760])/(solar_size_mw_AC*1000)
            else: 
                solar_power_norm_AC = np.zeros(8760)

            if grid_connection_scenario == 'off-grid':

                if solar_size_mw_AC == solar_sizes_mw_AC[-1] or wind_size_mw ==0:
                    wind_size_mw = 0
                    wind_cf_est = 0
                    run_wind_plant = False
                else:
                    wind_cf_est = hybrid_plant_cfest.wind.capacity_factor/100
                    wind_size_mw_calc = (electricity_production_target_MWhpyr/8760-solar_size_mw_AC*solar_cf_AC_est)/wind_cf_est
                    n_turbines = int(np.ceil(np.ceil(wind_size_mw_calc)/turbine_rating))
                    wind_size_mw = turbine_rating*n_turbines

                

                combined_vre_power_mWh = solar_power_norm_AC*solar_size_mw_AC +wind_power_norm*wind_size_mw

                #electrolyzer_capacity_EOL_MW = max(max(combined_vre_power_mWh),wind_size_mw_calc/(1+electrolyzer_degradation_power_increase))
                #electrolyzer_capacity_EOL_MW = max(max(combined_vre_power_mWh),wind_size_mw,solar_size_mw)
                electrolyzer_capacity_EOL_MW = max(combined_vre_power_mWh)
                electrolyzer_capacity_BOL_MW = electrolyzer_capacity_EOL_MW/(1+electrolyzer_degradation_power_increase)
                n_pem_clusters_max = int(np.ceil(np.ceil(electrolyzer_capacity_BOL_MW)/cluster_cap_mw))
                electrolyzer_size_mw = n_pem_clusters_max*cluster_cap_mw
                print('Solar size: ' +str(solar_size_mw_AC) + ' MW')
                print('Wind size: ' +str(wind_size_mw) + ' MW')
                print('Electrolyzer size: ' +str(electrolyzer_size_mw)+ ' MW')
                print('Estimated annual electricity production (MWh): '+ str(sum(combined_vre_power_mWh)))
                print('Battery size: ' + str(storage_size_mw) + ' MW, ' + str(storage_size_mwh) + ' MWh')

                kw_continuous = electrolyzer_size_mw * 1000
                load = [kw_continuous for x in
                        range(0, 8760)]  # * (sin(x) + pi) Set desired/required load profile for plant
                if battery_for_minimum_electrolyzer_op:
                    battery_dispatch_load = list(0.15*np.array(load))
                else:
                    battery_dispatch_load = list(np.array(load))

            # Run HOPP
            hopp_dict, plant_power_production, plant_shortfall_hopp, plant_curtailment_hopp, hybrid_plant, wind_size_mw, solar_size_mw_DC, lcoe = \
                hopp_tools_steel.run_HOPP(
                            project_path,
                            hopp_dict,
                            scenario,
                            site,
                            sample_site,
                            forced_sizes,
                            solar_size_mw_DC,
                            wind_size_mw,
                            storage_size_mw,
                            storage_size_mwh,
                            wind_cost_kw,
                            solar_cost_kw_DC,
                            storage_cost_kw,
                            storage_cost_kwh,
                            kw_continuous,
                            load,
                            electrolyzer_size_mw,
                            wind_om_cost_kw,
                            solar_om_cost_kw_DC,
                            nTurbs,
                            floris_config,
                            floris,
                            run_wind_plant
                        )
            
            solar_size_mw_AC = solar_size_mw_DC/solar_DC_AC_ratio

            print('Actual wnd/solar electricity output (MWh): ' + str(sum(plant_power_production)/1000))
            if run_wind_plant:
                cf_wind_annuals = hybrid_plant.wind._financial_model.Outputs.cf_annual_costs
                wind_itc_total = hybrid_plant.wind._financial_model.Outputs.itc_total
                wind_plant_power = hybrid_plant.wind.generation_profile[0:8759]
                if solar_size_mw_AC>0:
                    solar_plant_power = hybrid_plant.pv.generation_profile[0:len(wind_plant_power)]
                    cf_solar_annuals=hybrid_plant.pv._financial_model.Outputs.cf_annual_costs
                else:
                    cf_solar_annuals = np.zeros(30)
                #hopp_dict.main_dict['Configuration']['wind_plant_object']=hybrid_plant.wind
                if floris:
                    #ACTUAL WIND SIZE
                    hopp_dict.main_dict['Configuration']['n_Turbs']=hybrid_plant.wind._system_model.nTurbs
                    hopp_dict.main_dict['Configuration']['turb_rating_kw']=hybrid_plant.wind._system_model.turb_rating
                    hopp_dict.main_dict['Configuration']['wind_size_mw']=hybrid_plant.wind._system_model.nTurbs*hybrid_plant.wind._system_model.turb_rating*(1/1000)
                    wind_size_mw=hybrid_plant.wind._system_model.nTurbs*hybrid_plant.wind._system_model.turb_rating*(1/1000)
                    renewable_plant_cost['wind']['size_mw']=wind_size_mw
                combined_pv_wind_power_production_hopp = plant_power_production
            else:
                # solar_storage_only_lcoe=copy.copy(lcoe)
                if solar_size_mw_AC>0:
                    pv_plant_power = hybrid_plant.pv.generation_profile[0:len(wind_plant_power)]
                    combined_pv_wind_power_production_hopp = np.array(pv_plant_power)# + np.array(wind_plant_power)
                    cf_solar_annuals=hybrid_plant.pv._financial_model.Outputs.cf_annual_costs

                else:
                    combined_pv_wind_power_production_hopp= np.array(wind_plant_power) #plant_power_production+
                    cf_solar_annuals = np.zeros(30)

            energy_shortfall_hopp = [x - y for x, y in
                             zip(battery_dispatch_load,combined_pv_wind_power_production_hopp)]
            energy_shortfall_hopp = [x if x > 0 else 0 for x in energy_shortfall_hopp]
            combined_pv_wind_curtailment_hopp = [x - y for x, y in
                             zip(combined_pv_wind_power_production_hopp,load)]
            combined_pv_wind_curtailment_hopp = [x if x > 0 else 0 for x in combined_pv_wind_curtailment_hopp]
            combined_pv_wind_curtailment_hopp[0]=0


            #Step 5: Run Simple Dispatch Model
            hopp_dict, combined_pv_wind_storage_power_production_hopp, battery_SOC, battery_used, excess_energy = \
                hopp_tools_steel.run_battery(
                    hopp_dict,
                    energy_shortfall_hopp,
                    combined_pv_wind_curtailment_hopp,
                    combined_pv_wind_power_production_hopp
                )

            # grid information
            #TODO: This may change
            hopp_dict, cost_to_buy_from_grid, profit_from_selling_to_grid, energy_to_electrolyzer = hopp_tools_steel.grid(
                hopp_dict,
                combined_pv_wind_storage_power_production_hopp,
                sell_price,
                excess_energy,
                buy_price,
                kw_continuous,
                plot_grid,
            )

            print('Energy to electrolyzer after battery (MWh): ' + str(sum(energy_to_electrolyzer)/1000))
            print('Electricity production margin (%): ' + str(100*(sum(energy_to_electrolyzer)/1000 - electricity_production_target_MWhpyr)/electricity_production_target_MWhpyr))

            if solar_size_mw_AC > 0:
                cf_solar = hybrid_plant.pv.capacity_factor/100
                solar_annual_energy_MWh = hybrid_plant.annual_energies['pv']/1000
            else:
                cf_solar = 0
                solar_annual_energy_MWh = 0

            if wind_size_mw > 0:
                cf_wind = hybrid_plant.wind.capacity_factor/100
                wind_annual_energy_MWh = hybrid_plant.annual_energies['wind']/1000
            else:
                cf_wind = 0
                wind_annual_energy_MWh = 0

            # Step #: Calculate hydrogen pipe costs for distributed case
            if electrolysis_scale == 'Distributed':
                # High level estimate of max hydrogen flow rate. Doesn't have to be perfect, but should be slightly conservative (higher efficiency)
                hydrogen_max_hourly_production_kg = max(energy_to_electrolyzer)/electrolyzer_energy_kWh_per_kg

                # Run pipe cost analysis module
                pipe_network_cost_total_USD,pipe_network_costs_USD,pipe_material_cost_bymass_USD =\
                    distributed_pipe_cost_analysis.hydrogen_steel_pipeline_cost_analysis(parent_path,turbine_model,hydrogen_max_hourly_production_kg,site_name)

                pipeline_material_cost = pipe_network_costs_USD['Total material cost ($)'].sum()

                # Eventually replace with calculations
                if site_name == 'TX':
                    cabling_material_cost = 44553030

                if site_name == 'IA':
                    cabling_material_cost = 44514220
                if site_name == 'IN':
                    cabling_material_cost = 44553030
                if site_name == 'WY':
                    cabling_material_cost = 44514220
                if site_name == 'MS':
                    cabling_material_cost = 62751510
                if site_name == 'MN':
                    cabling_material_cost = 44514220
                transmission_cost = 0

                cabling_vs_pipeline_cost_difference = cabling_material_cost - pipeline_material_cost

                turbine_power_electronics_savings = 13

            elif electrolysis_scale == 'Centralized':
                cabling_vs_pipeline_cost_difference = 0
                cabling_material_cost =0
                pipeline_material_cost=0
                if grid_connection_scenario == 'hybrid-grid' or grid_connection_scenario == 'grid-only':

                    # Upload the right transmission cost CSV. Note, only works up to 1049 MW (files only go up to 1000 MW)
                    plant_step_size = 100
                    nearest_interconnect_size = int(np.round(interconnection_size_mw/plant_step_size))*plant_step_size
                    transmission_cost_df = pd.read_csv(os.path.join(project_path,'H2_Analysis','Transmission_costs',str(nearest_interconnect_size)+'MW_plant_transmission_costs.csv'),index_col = None,header = 0)

                    # Find the closest lat-lon in the transmission cost df
                    lat_lon = (site_df['Lat'],site_df['Lon'])
                    transmission_cost_lat_lons = [(x,y) for x,y in zip(transmission_cost_df['latitude'],transmission_cost_df['longitude'])]
                    transmission_cost_lat,transmission_cost_lon = transmission_cost_lat_lons[cdist([lat_lon],transmission_cost_lat_lons).argmin()]

                    trans_cap_cost_per_mw = transmission_cost_df.loc[(transmission_cost_df['latitude']==transmission_cost_lat) & (transmission_cost_df['longitude']==transmission_cost_lon),'trans_cap_cost_per_mw'].tolist()[0]
                    reinforcement_cost_per_mw = transmission_cost_df.loc[(transmission_cost_df['latitude']==transmission_cost_lat) & (transmission_cost_df['longitude']==transmission_cost_lon),'reinforcement_cost_per_mw'].tolist()[0]
                    transmission_cost = (trans_cap_cost_per_mw + reinforcement_cost_per_mw)*interconnection_size_mw

                else:
                    transmission_cost = 0

                turbine_power_electronics_savings = 0

            #revised_wind_renewable_cost = hybrid_plant.grid.total_installed_cost - cabling_vs_pipeline_cost_difference - turbine_power_electronics_savings*wind_size_mw*1000 + transmission_cost
            renewable_plant_cost['wind_savings_dollars']={'turbine_power_electronics_savings_dollars':-1*turbine_power_electronics_savings*wind_size_mw*1000,
            'tranmission_cost_dollars':transmission_cost,'cabling_vs_pipeline_cost_difference_dollars':-1*cabling_vs_pipeline_cost_difference}

            hopp_dict, H2_Results, electrical_generation_timeseries = hopp_tools_steel.run_H2_PEM_sim(
                hopp_dict,
                energy_to_electrolyzer,
                scenario,
                electrolyzer_size_mw,
                electrolysis_scale,
                n_pem_clusters,
                pem_control_type,
                electrolyzer_direct_cost_kw,
                electrolyzer_model_parameters,
                electrolyzer_degradation_penalty,
                grid_connection_scenario,
                hydrogen_production_capacity_required_kgphr

            )

                #Step 6b: Run desal model
            hopp_dict, desal_capex, desal_opex = hopp_tools_steel.desal_model(
                hopp_dict,
                H2_Results,
                electrolyzer_size_mw,
                electrical_generation_timeseries,
                useful_life,
            )

            hydrogen_annual_production = H2_Results['hydrogen_annual_output']

            print('Actual hydrogen annual production (kgpyr): ' + str(hydrogen_annual_production))
            print('Annual H2 production margin (%): ' + str(100*(hydrogen_annual_production - hydrogen_production_target_kgpy)/hydrogen_production_target_kgpy))

                # hydrogen_max_hourly_production_kg = max(H2_Results['hydrogen_hourly_production'])

                # Calculate required storage capacity to meet a flat demand profile. In the future, we could customize this to
                # work with any demand profile

            # Storage costs as a function of location
            if site_location == 'Site 1':
                storage_type = 'Buried pipes'
            elif site_location == 'Site 2':
                storage_type = 'Salt cavern'
            elif site_location == 'Site 3':
                storage_type = 'Buried pipes'
            elif site_location == 'Site 4':
                storage_type = 'Salt cavern'
            elif site_location == 'Site 5':
                storage_type = 'Salt cavern' #Unsure
            elif site_location == 'Site 7':
                storage_type = 'Lined rock cavern'

            hydrogen_production_storage_system_output_kgprhr,hydrogen_storage_capacity_kg,hydrogen_storage_capacity_MWh_HHV,hydrogen_storage_duration_hr,hydrogen_storage_cost_USDprkg,storage_compressor_total_capacity_kW,storage_compressor_total_installed_cost_USD,storage_status_message\
                 = hopp_tools_steel.hydrogen_storage_capacity_cost_calcs(H2_Results,electrolyzer_size_mw,storage_type,hydrogen_demand_kgphr)

            #Make sure there is enough wind capacity for storage compressor; if not, add wind capacity. Because we round up
            #to the nearest turbine size it is possible that there is already enough wind capacity; this bit just makes sure
            # that there will always be enough.

            if grid_connection_scenario == 'off-grid':
                combined_VRE_capacity_required_MW = electrolyzer_capacity_EOL_MW + storage_compressor_total_capacity_kW/1000

                combined_VRE_capacity_deficit = combined_VRE_capacity_required_MW - max(combined_vre_power_mWh)

                if combined_VRE_capacity_deficit > 0:
                    if solar_size_mw_AC == solar_sizes_mw_AC[-1] or wind_size_mw ==0:
                        if storage_size_mw == storage_sizes_mw[0]:
                            solar_size_mw_DC = solar_size_mw_DC + combined_VRE_capacity_deficit
                            solar_size_mw_AC = solar_size_mw_DC/solar_DC_AC_ratio
                            renewable_plant_cost['pv']['size_mw'] = solar_size_mw_AC
                    else:
                            n_turbines_extra = int(np.ceil(combined_VRE_capacity_deficit/turbine_rating))
                            wind_size_mw = wind_size_mw + turbine_rating*n_turbines_extra
                            renewable_plant_cost['wind']['size_mw']=wind_size_mw

            # if wind_capacity_required_MW > wind_size_mw:
            #     n_turbines = int(np.ceil(np.ceil(wind_capacity_required_MW)/turbine_rating))
            #     wind_size_mw = turbine_rating*n_turbines
            #     renewable_plant_cost['wind']['size_mw']=wind_size_mw

            # Apply storage multiplier
            hydrogen_storage_capacity_kg = hydrogen_storage_capacity_kg*storage_capacity_multiplier
            print(storage_status_message)

            # Run ProFAST to get LCOH

            # Municipal water rates and wastewater treatment rates combined ($/gal)
            if site_location == 'Site 1': # Site 1 - Indiana
                #water_cost = 0.00612
                water_cost = 0.0045
            elif site_location == 'Site 2': # Site 2 - Texas
                #water_cost = 0.00811
                water_cost = 0.00478
            elif site_location == 'Site 3': # Site 3 - Iowa
                #water_cost = 0.00634
                water_cost = 0.00291
            elif site_location == 'Site 4': # Site 4 - Mississippi
                #water_cost = 0.00844
                water_cost = 0.00409
            elif site_location =='Site 5': # Site 5 - MN, assuming same as IA for now
                #water_cost=0.00634 
                water_cost = 0.00291


            electrolyzer_efficiency_while_running = []
            water_consumption_while_running = []
            hydrogen_production_while_running = []
            for j in range(len(H2_Results['electrolyzer_total_efficiency'])):
                if H2_Results['hydrogen_hourly_production'][j] > 0:
                    electrolyzer_efficiency_while_running.append(H2_Results['electrolyzer_total_efficiency'][j])
                    water_consumption_while_running.append(H2_Results['water_hourly_usage'][j])
                    hydrogen_production_while_running.append(H2_Results['hydrogen_hourly_production'][j])
            # water_consumption_while_running=H2_Results['water_hourly_usage']
            # hydrogen_production_while_running=H2_Results['hydrogen_hourly_production']
            # Specify grid cost year for ATB year
            if atb_year == 2020:
                grid_year = 2025
            elif atb_year == 2025:
                grid_year = 2030
            elif atb_year == 2030:
                grid_year = 2035
            elif atb_year == 2035:
                grid_year = 2040

            # Read in csv for grid prices
            grid_prices = pd.read_csv(os.path.join(project_path, "H2_Analysis", grid_price_filename),index_col = None,header = 0)
            elec_price = grid_prices.loc[grid_prices['Year']==grid_year,site_name].tolist()[0]
            grid_prices_interpolated_USDperkwh = grid_price_interpolation(grid_prices,site_name,atb_year,useful_life,'kWh')


            # h2_solution,h2_summary,h2_price_breakdown,lcoh_breakdown,electrolyzer_installed_cost_kw,elec_cf,ren_frac,electrolyzer_total_EI_policy_grid,electrolysis_total_EI_policy_offgrid,H2_PTC,Ren_PTC,h2_production_capex = run_profast_for_hydrogen. run_profast_for_hydrogen(hopp_dict,electrolyzer_size_mw,H2_Results,\
            #                                 electrolyzer_capex_kw,time_between_replacement,electrolyzer_energy_kWh_per_kg,hydrogen_storage_capacity_kg,hydrogen_storage_cost_USDprkg,\
            #                                 desal_capex,desal_opex,useful_life,water_cost,wind_size_mw,solar_size_mw,storage_size_mw,renewable_plant_cost,wind_om_cost_kw,grid_connected_hopp,\
            #                                 grid_connection_scenario, atb_year, site_name, policy_option,policy,electrical_generation_timeseries, combined_pv_wind_power_production_hopp,combined_pv_wind_curtailment_hopp,\
            #                                 energy_shortfall_hopp,elec_price, grid_prices_interpolated_USDperkwh,grid_price_scenario,user_defined_stack_replacement_time,use_optimistic_pem_efficiency,wind_annual_energy_MWh,solar_annual_energy_MWh,solar_ITC)

            h2_solution,h2_summary,profast_h2_price_breakdown,lcoh_breakdown,electrolyzer_installed_cost_kw,elec_cf,ren_frac,electrolysis_total_EI_policy_grid,electrolysis_total_EI_policy_offgrid,H2_PTC,Ren_PTC,h2_production_capex,\
                                    hydrogen_storage_cost_USDprkg,hydrogen_storage_duration_hr,hydrogen_storage_capacity_kg,electrolyzer_size_mw = run_profast_for_hydrogen. run_profast_for_hydrogen(hopp_dict,electrolyzer_size_mw,H2_Results,\
                                    electrolyzer_capex_kw,time_between_replacement,electrolyzer_energy_kWh_per_kg,hydrogen_storage_capacity_kg,hydrogen_storage_cost_USDprkg,storage_compressor_total_capacity_kW,storage_compressor_total_installed_cost_USD,hydrogen_storage_duration_hr,\
                                    desal_capex,desal_opex,useful_life,water_cost,wind_size_mw,solar_size_mw_AC,storage_size_mw,renewable_plant_cost,wind_om_cost_kw,grid_connected_hopp,\
                                    grid_connection_scenario,atb_year, site_name, policy_option, policy,electrical_generation_timeseries, combined_pv_wind_storage_power_production_hopp,combined_pv_wind_curtailment_hopp,\
                                    energy_shortfall_hopp,elec_price,grid_prices_interpolated_USDperkwh, grid_price_scenario,user_defined_stack_replacement_time,use_optimistic_pem_efficiency,wind_annual_energy_MWh,solar_annual_energy_MWh,solar_ITC,gams_locations_rodeo_version,rodeo_output_dir,run_RODeO_selector)


            lcoh_init = h2_solution['price']
            if save_param_sweep_summary:
                lcoh_tracker.append(lcoh_init)
            pf_summary=h2_summary
            pf_breakdown=lcoh_breakdown

            # # Max hydrogen production rate [kg/hr]
            max_hydrogen_production_rate_kg_hr = np.max(H2_Results['hydrogen_hourly_production'])
            max_hydrogen_delivery_rate_kg_hr  = np.mean(H2_Results['hydrogen_hourly_production'])

            electrolyzer_capacity_factor = H2_Results['cap_factor']

            # Calculate hydrogen transmission cost and add to LCOH
            hopp_dict,h2_transmission_economics_from_profast,h2_transmission_economics_summary,h2_transmission_price,h2_transmission_price_breakdown = hopp_tools_steel.levelized_cost_of_h2_transmission(hopp_dict,max_hydrogen_production_rate_kg_hr,
            max_hydrogen_delivery_rate_kg_hr,electrolyzer_capacity_factor,atb_year,site_name,grid_price_filename)
            h2_transmission_price_tracker.append(h2_transmission_price)
            lcoh_final = lcoh_init + h2_transmission_price
            plant_cf=np.sum(combined_pv_wind_storage_power_production_hopp)/(1000*electrolyzer_size_mw*len(combined_pv_wind_storage_power_production_hopp))
            if save_param_sweep_summary:
                elec_cf_tracker.append(electrolyzer_capacity_factor)
                plant_cf_tracker.append(plant_cf)
            if lcoh_init<min_lcoh:
                lcoh_2return=lcoh_final
                best_case_desc=solar_desc + '-' + battery_desc
                best_hopp_dict=copy.copy(hopp_dict)
                best_result_ts_data=pd.DataFrame({
                'H2 Production [kg]': H2_Results['hydrogen_hourly_production'][0:len(energy_to_electrolyzer)],
                'Energy to Electrolyzer [kWh]':energy_to_electrolyzer,
                'Wind + PV [kWh]':combined_pv_wind_power_production_hopp,
                'Wind + PV + Battery [kWh]':combined_pv_wind_storage_power_production_hopp,
                'Wind + PV Curtailment [kWh]':combined_pv_wind_curtailment_hopp,
                'Battery SOC [kWh]':battery_SOC,
                'Battery Used [kWh]':battery_used,
                'Battery Load [kWh]':battery_dispatch_load[0:len(battery_SOC)]})
                best_result_annual_data=pd.Series({'LCOH [$/kg]':lcoh_init,
                'Electrolyzer CF':electrolyzer_capacity_factor,
                'HPP CF':plant_cf,
                'H2 [kg/year]':hydrogen_annual_production,
                'H2 Transmission [$/kg]':h2_transmission_price,
                'Cable Cost [$]':cabling_material_cost,
                'Pipeline Cost [$]':pipeline_material_cost,
                'Transmission Cost [$]':transmission_cost,
                'Power Electronic Savings [$]':turbine_power_electronics_savings*wind_size_mw*1000,
                })

                lcoh_info_profast=pf_breakdown
                h2_performance=H2_Results
                h2_ts=hopp_dict.main_dict['Models']['run_H2_PEM_sim']['output_dict']['H2_TimeSeries']
                h2_agg=hopp_dict.main_dict['Models']['run_H2_PEM_sim']['output_dict']['H2_AggData']
                #h2_agg=h2_agg.drop('IV curve coeff',axis=0)
                hydrogen_storage_data=pd.Series({'H2 Storage Output [kg/hr]':hydrogen_production_storage_system_output_kgprhr,
                'H2 Storage Capacity [kg]':hydrogen_storage_capacity_kg,
                'H2 Storage Capacity [MWh HHV]':hydrogen_storage_capacity_MWh_HHV,
                'H2 Storage Duration [hr]':hydrogen_storage_duration_hr,
                'H2 Storage Cost [$/kg]':hydrogen_storage_cost_USDprkg})

                # Re-set bestcase results to return to main script
                combined_pv_wind_power_production_hopp_best = combined_pv_wind_power_production_hopp
                combined_pv_wind_storage_power_production_hopp_best = combined_pv_wind_storage_power_production_hopp
                combined_pv_wind_curtailment_hopp_best = combined_pv_wind_curtailment_hopp
                energy_shortfall_hopp_best = hopp_dict.main_dict["Models"]["grid"]["ouput_dict"]['energy_from_the_grid']
                energy_to_electrolyzer_best = energy_to_electrolyzer
                electrolyzer_size_mw_best = electrolyzer_size_mw
                hybrid_plant_best = hybrid_plant
                solar_size_mw_best = solar_size_mw_AC
                wind_size_mw_best = wind_size_mw
                storage_size_mw_best = storage_size_mw
                storage_size_mwh_best = storage_size_mwh
                renewable_plant_cost_best = renewable_plant_cost
                lcoe_best = lcoe
                cost_to_buy_from_grid_best = cost_to_buy_from_grid
                profit_from_selling_to_grid_best = profit_from_selling_to_grid
                cf_solar_annuals_best = cf_solar_annuals


            min_lcoh=np.min([min_lcoh,lcoh_init])
    #end=time.perf_counter()
    #print('Took {} sec to run parameter sweep'.format(round(end-start,3)))
    best_result_data={'HOPP_dict':best_hopp_dict,
    'Time-Series Info':best_result_ts_data,
    'Annual Info':best_result_annual_data,
    'H2 Storage Info':hydrogen_storage_data,
    'ProFAST LCOH Breakdown':lcoh_info_profast,
    'H2 Results':h2_performance,
    'H2 Aggregate Data':h2_agg,
    'H2 Time Series Info':h2_ts}
    param_folder_name=results_dir + '/PV_PS/'
    if not os.path.exists(param_folder_name):
        os.mkdir(param_folder_name)

        []
    if save_best_solar_case_pickle:
        if electrolyzer_degradation_penalty:
            deg_desc='Degradaded_'
        else:
            deg_desc='Undegraded_'
        filename_desc=grid_connection_scenario + '_' + electrolysis_scale + '_' +site_name + '_{}_Wind{}_'.format(atb_year,round(wind_size_mw)) + best_case_desc + '_' + pem_control_type + 'Control' + '_{}stacks_'.format(n_pem_clusters) + deg_desc + policy_option.replace(' ','-')
        filename=filename_desc + '.pickle'

        df=pd.Series(best_result_data)
        df.to_pickle(param_folder_name + filename)
        # import pickle
        # with open(results_dir + filename,'wb') as handle:
        #     pickle.dump(best_result_data,handle,protocol=pickle.HIGHEST_PROTOCOL)
        print('Saved best case solar & battery scenario information to...' )
        print('Folder: '+ param_folder_name)
        print('Filename: ' + filename)
    

    if save_param_sweep_summary:
        param_sweep_desc=grid_connection_scenario + '_' + electrolysis_scale + '_' +site_name + '_{}_Wind{}'.format(atb_year,wind_size_mw) + '_' + pem_control_type + 'Control' + '{}_Stacks'.format(n_pem_clusters) + deg_desc + policy_option.replace(' ','-')
        param_sweep_tracked_df=pd.DataFrame({
            'Solar Size [MW]':solar_size_tracker,'Battery Charge Rate [MW]':battery_chargeRate_tracker,
            'Battery Storage Hours':battery_hour_tracker,
            'LCOH [$/kg]':lcoh_tracker,'H2 Transmission Cost [$/kg]':h2_transmission_price_tracker,
            'HPP CF':plant_cf_tracker,'Electrolyzer CF':elec_cf_tracker})
        param_sweep_tracked_df.to_csv(param_folder_name + 'SolarSweep_'+param_sweep_desc + '.csv')
        param_sweep_tracked_df.to_pickle(param_folder_name + 'SolarSweep_'+param_sweep_desc )
    else:
        param_sweep_tracked_df = None

    return lcoh_2return,best_hopp_dict,best_result_data,param_sweep_tracked_df,\
            combined_pv_wind_power_production_hopp_best,combined_pv_wind_storage_power_production_hopp_best,\
            combined_pv_wind_curtailment_hopp_best,energy_shortfall_hopp_best,energy_to_electrolyzer_best,\
            hybrid_plant_best,solar_size_mw_best,wind_size_mw_best,storage_size_mw_best,storage_size_mwh_best,electrolyzer_size_mw_best,renewable_plant_cost_best,lcoe_best,\
            cost_to_buy_from_grid_best,profit_from_selling_to_grid_best,cf_wind_annuals,cf_solar_annuals_best,wind_itc_total
