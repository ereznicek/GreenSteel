# general imports
from distutils.command.config import config
import os
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy_financial as npf
import sys
from scipy import optimize
from time import time
from pprint import pprint

# yaml imports
import yaml
from yamlinclude import YamlIncludeConstructor 
from pathlib import Path

PATH = Path(__file__).parent
YamlIncludeConstructor.add_to_loader_class(loader_class=yaml.FullLoader, base_dir=PATH / '../../input/floris/')
YamlIncludeConstructor.add_to_loader_class(loader_class=yaml.FullLoader, base_dir=PATH / '../../input/turbines/')

# visualization imports
import matplotlib.pyplot as plt

# packages needed for setting NREL API key
from hopp.keys import set_developer_nrel_gov_key, get_developer_nrel_gov_key

# ORBIT imports 
from ORBIT import ProjectManager, load_config
from ORBIT.core.library import initialize_library
initialize_library(os.path.join(os.getcwd(), "../../input/"))

# HOPP imports 
import hopp.eco.electrolyzer as he_elec
import hopp.eco.finance as he_fin
import hopp.eco.hopp_mgmt as he_hopp
import hopp.eco.utilities as he_util
import hopp.eco.hydrogen_mgmt as he_h2

# ################ Set API key
#global NREL_API_KEY
#NREL_API_KEY = os.getenv("NREL_API_KEY")

#set_developer_nrel_gov_key(NREL_API_KEY)  # Set this key manually here if you are not setting it using the .env or with an env var
    
# set up function to run base line case
def run_simulation(electrolyzer_rating=None, plant_size=None, verbose=False, show_plots=False, save_plots=True, use_profast=True, storage_type=None, turbine_model=None, incentive_option=1, plant_design_scenario=1, output_level=1, location="", grid_connection=None, days=None):

    # load inputs as needed
    if location !="":
        location = "_0"+str(location)
    turbine_model = str(turbine_model)
    filename_turbine_config = "../../input/turbines/"+turbine_model+".yaml"
    filename_orbit_config = "../../input/plant/orbit-config-"+turbine_model+location+".yaml"
    filename_floris_config = "../../input/floris/floris_input_iea_"+turbine_model+ ".yaml"
    plant_config, turbine_config, wind_resource, floris_config = he_util.get_inputs(filename_orbit_config=filename_orbit_config, filename_floris_config=filename_floris_config , filename_turbine_config=filename_turbine_config, verbose=verbose, show_plots=show_plots, save_plots=save_plots)

    if electrolyzer_rating != None:
        plant_config["electrolyzer"]["rating"] = electrolyzer_rating

    if storage_type != None:
        plant_config["h2_storage"]["type"] = storage_type
        plant_config["h2_storage"]["days"] = days

    if plant_size != None:
        plant_config["plant"]["capacity"] = plant_size
        plant_config["plant"]["num_turbines"] = int(plant_size/turbine_config["turbine_rating"])
        print(plant_config["plant"]["num_turbines"])

    # 7 scenarios, 3 discrete variables
    design_scenario = plant_config["plant_design"]["scenario%s" %(plant_design_scenario)]
    design_scenario["id"] = plant_design_scenario

    if design_scenario["h2_storage_location"] == "turbine":
        plant_config["h2_storage"]["type"] = "turbine"

    # run orbit for wind plant construction and other costs
    ## TODO get correct weather (wind, wave) inputs for ORBIT input (possibly via ERA5)
    orbit_project = he_fin.run_orbit(plant_config, weather=None, verbose=verbose)
    df_detailed_outputs = pd.DataFrame(orbit_project.detailed_outputs)
    df_detailed_outputs.to_csv("data/orbit_costs/"+location+"_detailed_orbit_outputs.csv")
    df_detailed_capex = pd.DataFrame.from_dict(orbit_project.capex_breakdown_per_kw, orient='index')
    df_detailed_capex.to_csv("data/orbit_costs/"+location+"_detailed_orbit_capex_per_kw.csv")
    
    # setup HOPP model
    hopp_site, hopp_technologies, hopp_scenario, hopp_h2_args = he_hopp.setup_hopp(plant_config, turbine_config, wind_resource, orbit_project, floris_config, show_plots=show_plots, save_plots=save_plots)

    # run HOPP model
    hopp_results = he_hopp.run_hopp(hopp_site, hopp_technologies, hopp_scenario, hopp_h2_args, verbose=verbose)

    # this portion of the system is inside a function so we can use a solver to determine the correct energy availability for h2 production
    def energy_internals(hopp_results=hopp_results, hopp_site=hopp_site, hopp_technologies=hopp_technologies, hopp_scenario=hopp_scenario, hopp_h2_args=hopp_h2_args, orbit_project=orbit_project, design_scenario=design_scenario, plant_config=plant_config, turbine_config=turbine_config, wind_resource=wind_resource, floris_config=floris_config, electrolyzer_rating=electrolyzer_rating, plant_size=plant_size, verbose=verbose, show_plots=show_plots, save_plots=save_plots, use_profast=use_profast, storage_type=storage_type, incentive_option=incentive_option, plant_design_scenario=plant_design_scenario, output_level=output_level, solver=True, power_for_peripherals_kw_in=0.0, breakdown=False):

        hopp_results_internal = dict(hopp_results)

        # set energy input profile
        ### subtract peripheral power from supply to get what is left for electrolyzer
        remaining_power_profile_in = np.zeros_like(hopp_results["combined_pv_wind_power_production_hopp"])
        for i in range(len(hopp_results["combined_pv_wind_power_production_hopp"])):
            r = hopp_results["combined_pv_wind_power_production_hopp"][i] - power_for_peripherals_kw_in
            if r > 0:
                # print(r)
                remaining_power_profile_in[i] = r

        hopp_results_internal["combined_pv_wind_power_production_hopp"] = tuple(remaining_power_profile_in)
        
        # run electrolyzer physics model
        electrolyzer_physics_results = he_elec.run_electrolyzer_physics(hopp_results_internal, hopp_scenario, hopp_h2_args, plant_config, wind_resource, design_scenario, show_plots=show_plots, save_plots=save_plots, verbose=verbose)

        # run electrolyzer cost model
        electrolyzer_cost_results = he_elec.run_electrolyzer_cost(electrolyzer_physics_results, hopp_scenario, plant_config, design_scenario, verbose=verbose)
        
        desal_results = he_elec.run_desal(plant_config, electrolyzer_physics_results, design_scenario, verbose)

        # run array system model
        h2_pipe_array_results = he_h2.run_h2_pipe_array(plant_config, orbit_project, electrolyzer_physics_results, design_scenario, verbose)

        # compressor #TODO size correctly
        h2_transport_compressor, h2_transport_compressor_results = he_h2.run_h2_transport_compressor(plant_config, electrolyzer_physics_results, design_scenario, verbose=verbose)

        # transport pipeline
        h2_transport_pipe_results = he_h2.run_h2_transport_pipe(plant_config, electrolyzer_physics_results, design_scenario, verbose=verbose)

        # pressure vessel storage
        pipe_storage, h2_storage_results = he_h2.run_h2_storage(plant_config, turbine_config, electrolyzer_physics_results, design_scenario, verbose=verbose)
        
        total_energy_available = np.sum(hopp_results["combined_pv_wind_power_production_hopp"])
        
        ### get all energy non-electrolyzer usage in kw
        desal_power_kw = desal_results["power_for_desal_kw"]

        h2_transport_compressor_power_kw = h2_transport_compressor_results["compressor_power"] # kW

        h2_storage_energy_kwh = h2_storage_results["storage_energy"] 
        h2_storage_power_kw = h2_storage_energy_kwh*(1.0/(365*24))
        
        # if transport is not HVDC and h2 storage is on shore, then power the storage from the grid
        if (design_scenario["transportation"] == "pipeline") and (design_scenario["h2_storage_location"] == "onshore"):
            total_accessory_power_renewable_kw = desal_power_kw + h2_transport_compressor_power_kw
            total_accessory_power_grid_kw = h2_storage_power_kw
        else:
            total_accessory_power_renewable_kw = desal_power_kw + h2_transport_compressor_power_kw + h2_storage_power_kw
            total_accessory_power_grid_kw = 0.0

        ### subtract peripheral power from supply to get what is left for electrolyzer and also get grid power
        remaining_power_profile = np.zeros_like(hopp_results["combined_pv_wind_power_production_hopp"])
        grid_power_profile = np.zeros_like(hopp_results["combined_pv_wind_power_production_hopp"])
        for i in range(len(hopp_results["combined_pv_wind_power_production_hopp"])):
            r = hopp_results["combined_pv_wind_power_production_hopp"][i] - total_accessory_power_renewable_kw
            grid_power_profile[i] = total_accessory_power_grid_kw
            if r > 0:
                remaining_power_profile[i] = r

        if verbose and not solver:
            print("\nEnergy/Power Results:")
            print("Supply (MWh): ", total_energy_available)
            print("Desal (kW): ", desal_power_kw)
            print("Transport compressor (kW): ", h2_transport_compressor_power_kw)
            print("Storage compression, refrigeration, etc (kW): ", h2_storage_power_kw)

        if (show_plots or save_plots) and not solver:
            fig, ax = plt.subplots(1)
            plt.plot(np.asarray(hopp_results["combined_pv_wind_power_production_hopp"])*1E-6, label="Total Energy Available")
            plt.plot(remaining_power_profile*1E-6, label="Energy Available for Electrolysis")
            plt.xlabel("Hour")
            plt.ylabel("Power (GW)")
            plt.tight_layout()
            if save_plots:
                savepath = "figures/power_series/"
                if not os.path.exists(savepath):
                    os.makedirs(savepath)
                plt.savefig(savepath+"power_%i.png" %(design_scenario["id"]), transparent=True)
            if show_plots:
                plt.show()
        if solver:
            if breakdown:
                return total_accessory_power_renewable_kw, total_accessory_power_grid_kw, desal_power_kw, h2_transport_compressor_power_kw, h2_storage_power_kw
            else:
                return total_accessory_power_renewable_kw
        else:
            return electrolyzer_physics_results, electrolyzer_cost_results, desal_results, h2_pipe_array_results, h2_transport_compressor, h2_transport_compressor_results, h2_transport_pipe_results, pipe_storage, h2_storage_results, total_accessory_power_renewable_kw, total_accessory_power_grid_kw

    # define function to provide to the brent solver
    def energy_residual_function(power_for_peripherals_kw_in):

        # get results for current design
        # print("power peri in: ", power_for_peripherals_kw_in)
        power_for_peripherals_kw_out = energy_internals(power_for_peripherals_kw_in=power_for_peripherals_kw_in, solver=True, verbose=False)

        # collect residual
        power_residual = power_for_peripherals_kw_out - power_for_peripherals_kw_in
        # print("\nresidual: ", power_residual)

        return power_residual

    def simple_solver(initial_guess=0.0):

        # get results for current design
        total_accessory_power_renewable_kw, total_accessory_power_grid_kw, desal_power_kw, h2_transport_compressor_power_kw, h2_storage_power_kw  = energy_internals(power_for_peripherals_kw_in=initial_guess, solver=True, verbose=False, breakdown=True)
        
        return total_accessory_power_renewable_kw, total_accessory_power_grid_kw, desal_power_kw, h2_transport_compressor_power_kw, h2_storage_power_kw
    
    #################### solving for energy needed for non-electrolyzer components ####################################
    # this approach either exactly over over-estimates the energy needed for non-electrolyzer components
    solver_results = simple_solver(0)
    solver_result = solver_results[0]

    # this is a check on the simple solver
    print("\nsolver result: ", solver_result)
    # residual = energy_residual_function(solver_result)
    # print("\nresidual: ", residual)

    # this approach exactly sizes the energy needed for the non-electrolyzer components (according to the current models anyway)
    # solver_result = optimize.brentq(energy_residual_function, -10, 20000, rtol=1E-5)
    # OptimizeResult = optimize.root(energy_residual_function, 11E3, tol=1)
    # solver_result = OptimizeResult.x
    # print(solver_result)

    ##################################################################################################################

    # get results for final design
    electrolyzer_physics_results, electrolyzer_cost_results, desal_results, h2_pipe_array_results, h2_transport_compressor, h2_transport_compressor_results, h2_transport_pipe_results, pipe_storage, h2_storage_results, total_accessory_power_renewable_kw, total_accessory_power_grid_kw \
        = energy_internals(solver=False, power_for_peripherals_kw_in=solver_result)
    
    ## end solver loop here
    platform_results = he_h2.run_equipment_platform(plant_config, design_scenario, electrolyzer_physics_results, h2_storage_results, desal_results, verbose=verbose)
    
    ################# OSW intermediate calculations" aka final financial calculations
    # does LCOE even make sense if we are only selling the H2? I think in this case LCOE should not be used, rather LCOH should be used. Or, we could use LCOE based on the electricity actually used for h2
    # I think LCOE is just being used to estimate the cost of the electricity used, but in this case we should just use the cost of the electricity generating plant since we are not selling to the grid. We
    # could build in a grid connection later such that we use LCOE for any purchased electricity and sell any excess electricity after H2 production
    # actually, I think this is what OSW is doing for LCOH
    
    # TODO double check full-system CAPEX
    capex, capex_breakdown = he_fin.run_capex(hopp_results, orbit_project, electrolyzer_cost_results, h2_pipe_array_results, h2_transport_compressor_results, h2_transport_pipe_results, h2_storage_results, plant_config, design_scenario, desal_results, platform_results, verbose=verbose)

    # TODO double check full-system OPEX
    opex_annual, opex_breakdown_annual = he_fin.run_opex(hopp_results, orbit_project, electrolyzer_cost_results, h2_pipe_array_results, h2_transport_compressor_results, h2_transport_pipe_results, h2_storage_results, plant_config, desal_results, platform_results, verbose=verbose, total_export_system_cost=capex_breakdown["electrical_export_system"])

    print("wind capacity factor: ", np.sum(hopp_results["combined_pv_wind_power_production_hopp"])*1E-3/(plant_config["plant"]["capacity"]*365*24))

    if use_profast:
        lcoe, pf_lcoe = he_fin.run_profast_lcoe(plant_config, orbit_project, capex_breakdown, opex_breakdown_annual, hopp_results, design_scenario, verbose=verbose, show_plots=show_plots, save_plots=save_plots)
        lcoh_grid_only, pf_grid_only = he_fin.run_profast_grid_only(plant_config, orbit_project, electrolyzer_physics_results, capex_breakdown, opex_breakdown_annual, hopp_results, design_scenario, total_accessory_power_renewable_kw, total_accessory_power_grid_kw, verbose=verbose, show_plots=show_plots, save_plots=save_plots)
        lcoh, pf_lcoh = he_fin.run_profast_full_plant_model(plant_config, orbit_project, electrolyzer_physics_results, capex_breakdown, opex_breakdown_annual, hopp_results, incentive_option, design_scenario, total_accessory_power_renewable_kw, total_accessory_power_grid_kw, verbose=verbose, show_plots=show_plots, save_plots=save_plots)
    
    ################# end OSW intermediate calculations
    power_breakdown = he_util.post_process_simulation(lcoe, lcoh, pf_lcoh, pf_lcoe, hopp_results, electrolyzer_physics_results, plant_config, h2_storage_results, capex_breakdown, opex_breakdown_annual, orbit_project, platform_results, desal_results, design_scenario, plant_design_scenario, incentive_option, solver_results=solver_results, show_plots=show_plots, save_plots=save_plots)#, lcoe, lcoh, lcoh_with_grid, lcoh_grid_only)
    
    # return
    if output_level == 0:
        return 0
    elif output_level == 1:
        return lcoh
    elif output_level == 2:
        return lcoh, lcoe, capex_breakdown, opex_breakdown_annual, pf_lcoh, electrolyzer_physics_results
    elif output_level == 3:
        return lcoh, lcoe, capex_breakdown, opex_breakdown_annual, pf_lcoh, electrolyzer_physics_results, pf_lcoe, power_breakdown

def run_sweeps(simulate=False, verbose=True, show_plots=True, use_profast=True):

    if simulate:
        verbose = False 
        show_plots = False 
    if simulate:
        storage_types = ["none", "pressure_vessel", "pipe", "salt_cavern"]
        plant_sizes = [400]#, 800, 1200] #[200, 400, 600, 800]

        for plant_size in plant_sizes:
            ratings = np.linspace(round(0.2*plant_size, ndigits=0), 2*plant_size + 1, 50)
            for storage_type in storage_types:
                lcoh_array = np.zeros(len(ratings))
                for z in np.arange(0,len(ratings)):
                    lcoh_array[z] = run_simulation(electrolyzer_rating=ratings[z], plant_size=plant_size, verbose=verbose, show_plots=show_plots, use_profast=use_profast, storage_type=storage_type)
                    print(lcoh_array)
                np.savetxt("data/lcoh_vs_rating_%s_storage_%sMWwindplant.txt" %(storage_type, plant_size), np.c_[ratings, lcoh_array])

    if show_plots:

        plant_sizes = [400, 800, 1200]#[200, 400, 600, 800]
        indexes = [(0,0), (0,1), (1,0), (1,1)]
        fig, ax = plt.subplots(2, 2, sharex=True, sharey=True, figsize=(10,6))

        for i in np.arange(0, len(plant_sizes)):
            plant_size = plant_sizes[i]
            data_no_storage = np.loadtxt("data/lcoh_vs_rating_none_storage_%sMWwindplant.txt" %(plant_size))
            data_pressure_vessel = np.loadtxt("data/lcoh_vs_rating_pressure_vessel_storage_%sMWwindplant.txt" %(plant_size))
            data_salt_cavern = np.loadtxt("data/lcoh_vs_rating_salt_cavern_storage_%sMWwindplant.txt" %(plant_size))
            data_pipe = np.loadtxt("data/lcoh_vs_rating_pipe_storage_%sMWwindplant.txt" %(plant_size))
            # print(indexes[i][0], indexes[i][1])
            # print(ax[indexes[i][0], indexes[i][1]])
            ax[indexes[i]].plot(data_pressure_vessel[:,0]/plant_size, data_pressure_vessel[:,1], label="Pressure Vessel")
            ax[indexes[i]].plot(data_pipe[:,0]/plant_size, data_pipe[:,1], label="Underground Pipe")
            ax[indexes[i]].plot(data_salt_cavern[:,0]/plant_size, data_salt_cavern[:,1], label="Salt Cavern")
            ax[indexes[i]].plot(data_no_storage[:,0]/plant_size, data_no_storage[:,1], "--k", label="No Storage")

            ax[indexes[i]].scatter(data_pressure_vessel[np.argmin(data_pressure_vessel[:,1]),0]/plant_size, np.min(data_pressure_vessel[:,1]), color="k")
            ax[indexes[i]].scatter(data_pipe[np.argmin(data_pipe[:,1]),0]/plant_size, np.min(data_pipe[:,1]), color="k")
            ax[indexes[i]].scatter(data_salt_cavern[np.argmin(data_salt_cavern[:,1]),0]/plant_size, np.min(data_salt_cavern[:,1]), color="k")
            ax[indexes[i]].scatter(data_no_storage[np.argmin(data_no_storage[:,1]),0]/plant_size, np.min(data_no_storage[:,1]), color="k", label="Optimal ratio")

            ax[indexes[i]].legend(frameon=False, loc="best")

            ax[indexes[i]].set_xlim([0.2,2.0])
            ax[indexes[i]].set_ylim([0,25])

            ax[indexes[i]].annotate("%s MW Wind Plant" %(plant_size), (0.6, 1.0))

            print(data_pressure_vessel)
            print(data_salt_cavern)

        ax[1,0].set_xlabel("Electrolyzer/Wind Plant Rating Ratio")
        ax[1,1].set_xlabel("Electrolyzer/Wind Plant Rating Ratio")
        ax[0,0].set_ylabel("LCOH ($/kg)")
        ax[1,0].set_ylabel("LCOH ($/kg)")



        plt.tight_layout()
        plt.savefig("lcoh_vs_rating_ratio.pdf", transparent=True)
        plt.show()

    return 0

def run_policy_options_storage_types(verbose=True, show_plots=False, save_plots=False,  use_profast=True):

    storage_types = ["pressure_vessel", "pipe", "salt_cavern", "none"]
    policy_options = [1, 2, 3, 4, 5, 6, 7]

    lcoh_array = np.zeros((len(storage_types), len(policy_options)))
    for i, storage_type in enumerate(storage_types):
        for j, poption in enumerate(policy_options):
            lcoh_array[i, j] = run_simulation(storage_type=storage_type, incentive_option=poption, verbose=verbose, show_plots=show_plots, use_profast=use_profast)
        print(lcoh_array)

    savepath = "results/"
    if not os.path.exists(savepath):
        os.makedirs(savepath)
    np.savetxt(savepath+"lcoh-with-policy.txt", np.c_[np.round(lcoh_array, decimals=2)], header="rows: %s, columns: %s" %("".join(storage_types), "".join(str(p) for p in policy_options)), fmt="%.2f")

    return 0

def run_policy_storage_design_options(verbose=False, show_plots=False, save_plots=False,  use_profast=True):

    design_scenarios = [1,7]
    policy_options = [1,2,3]
    storage_types = ["none"]

    design_series = []
    policy_series = []
    storage_series = []
    lcoh_series = []
    lcoe_series = []
    electrolyzer_capacity_factor_series = []
    annual_energy_breakdown_series  = {"design": [],
                                "policy": [],
                                "storage": [],
                                "wind_kwh": [],
                                "electrolyzer_kwh": [],
                                "desal_kwh": [],
                                "h2_transport_compressor_power_kwh": [], 
                                "h2_storage_power_kwh": []}

    lcoh_array = np.zeros((len(design_scenarios), len(policy_options)))
    for i, design in enumerate(design_scenarios):
        for j, policy in enumerate(policy_options):
            for storage in storage_types:
                if (storage != "pressure_vessel"):# and storage != "none"):
                    if (design != 1 and design != 5 and design != 7):
                        print("skipping: ", design, " ", policy, " ", storage)
                        continue
                design_series.append(design)
                policy_series.append(policy)
                storage_series.append(storage)
                lcoh, lcoe, capex_breakdown, opex_breakdown_annual, pf_lcoh, electrolyzer_physics_results, pf_lcoe, annual_energy_breakdown \
                    = run_simulation(storage_type=storage, plant_design_scenario=design, incentive_option=policy, verbose=verbose, show_plots=show_plots, use_profast=use_profast, output_level=3)
                lcoh_series.append(lcoh)
                lcoe_series.append(lcoe)
                electrolyzer_capacity_factor_series.append(electrolyzer_physics_results["capacity_factor"])

                annual_energy_breakdown_series["design"].append(design)
                annual_energy_breakdown_series["policy"].append(policy)
                annual_energy_breakdown_series["storage"].append(storage)
                for key in annual_energy_breakdown.keys():
                    annual_energy_breakdown_series[key].append(annual_energy_breakdown[key])

    savepath = "data/"
    if not os.path.exists(savepath):
        os.makedirs(savepath)
    df = pd.DataFrame.from_dict({"Design": design_series, "Storage": storage_series, "Policy": policy_series,"LCOH [$/kg]": lcoh_series, "LCOE [$/kWh]": lcoe_series, "Electrolyzer capacity factor": electrolyzer_capacity_factor_series})
    df.to_csv(savepath+"design-storage-policy-lcoh.csv")

    df_energy = pd.DataFrame.from_dict(annual_energy_breakdown_series)
    df_energy.to_csv(savepath+"annual_energy_breakdown.csv")
    return 0

def run_design_options(verbose=False, show_plots=False, save_plots=True,  incentive_option=1):

    design_options = range(1,8) # 8
    scenario_lcoh = []
    scenario_lcoe = []
    scenario_capex_breakdown = []
    scenario_opex_breakdown_annual = []
    scenario_pf = []
    scenario_electrolyzer_physics = []

    for design in design_options:
        lcoh, lcoe, capex_breakdown, opex_breakdown_annual, pf, electrolyzer_physics_results = run_simulation(verbose=verbose, show_plots=show_plots, save_plots=save_plots,use_profast=True, incentive_option=incentive_option, plant_design_scenario=design, output_level=2)
        scenario_lcoh.append(lcoh)
        scenario_lcoe.append(lcoe)
        scenario_capex_breakdown.append(capex_breakdown)
        scenario_opex_breakdown_annual.append(opex_breakdown_annual)
        scenario_pf.append(pf)
        scenario_electrolyzer_physics.append(electrolyzer_physics_results)

    df_aggregate = pd.DataFrame.from_dict({"Design": design_options, "LCOH [$/kg]": scenario_lcoh, "LCOE [$/kWh]": scenario_lcoe})
    df_capex = pd.DataFrame(scenario_capex_breakdown)
    df_opex = pd.DataFrame(scenario_opex_breakdown_annual)

    df_capex.insert(0, 'Design', design_options)
    df_opex.insert(0, 'Design', design_options)

    # df_aggregate = df_aggregate.transpose()
    df_capex = df_capex.transpose()
    df_opex = df_opex.transpose()

    results_path = "./combined_results/"
    if not os.path.exists(results_path):
        os.mkdir(results_path)
    df_aggregate.to_csv(results_path+"metrics.csv")
    df_capex.to_csv(results_path+"capex.csv")
    df_opex.to_csv(results_path+"opex.csv")
    print(df_aggregate)
    print(df_capex)
    print(df_opex)
    return 0
def run_storage_options(verbose=True, show_plots=False, save_plots=False,  use_profast=True):
    sites = ["Gulf of Mexico", 
    "Central Atlantic", 
    "New York Bight", 
    "California"
    ]
    policies = ["Base", 
    ]
    designs = ["Onshore H2", 
    "Offshore H2"]
    turbine_model = [
    "osw_18MW"
    ]
    storage_types = ["pipe", "pressure_vessel", "salt_cavern"
                ]
    days_of_storage = [1,3,11]

    days_of_storage_series = []
    design_series = []
    policy_series = []
    site_series = []
    storage_series = []
    turbine_series = []
    lcoh_series = []
    lcoe_series = []
    electrolyzer_capacity_factor_series = []
    for turbine in turbine_model:
        print(turbine)
        for (i, site) in enumerate([1,2,3,4]):
            for (j, plant_design) in enumerate([1,7]):
                for storage in storage_types:
                    for days in days_of_storage:
                        for (k, policy) in enumerate([1]):
                            site_series.append(sites[i])
                            design_series.append(designs[j])
                            turbine_series.append(turbine)
                            policy_series.append(policies[k])
                            storage_series.append(storage)
                            days_of_storage_series.append(days)
                            lcoh, lcoe, capex_breakdown, opex_breakdown_annual, pf_lcoh, electrolyzer_physics_results, pf_lcoe, annual_energy_breakdown \
                                = run_simulation(storage_type=storage,days=days,save_plots=save_plots, turbine_model=turbine, plant_design_scenario=plant_design, incentive_option=policy, verbose=verbose, show_plots=show_plots, use_profast=use_profast,location=site, output_level=3)
                        
                            lcoh_series.append(lcoh)
                            lcoe_series.append(lcoe)
                            electrolyzer_capacity_factor_series.append(electrolyzer_physics_results["capacity_factor"])



    savepath = "data/"
    if not os.path.exists(savepath):
        os.makedirs(savepath)
    df = pd.DataFrame.from_dict({"Site": site_series,"Design": design_series, "Storage": storage_series,"Days of Storage": days_of_storage_series, "Policy": policy_series,"LCOH [$/kg]": lcoh_series, "LCOE [$/kWh]": lcoe_series, "Electrolyzer capacity factor": electrolyzer_capacity_factor_series})
    df.to_csv(savepath+"design-storage-policy-lcoh.csv")



def run_for_greensteel_lcoh(verbose=True, show_plots=False, save_plots=True,  use_profast=True):
    sites = ["Gulf of Mexico", 
    # "Central Atlantic", 
    # "New York Bight", 
    # "California"
    ]

    policies = ["Base", 
    # "Min", 
    # "Max"
    ]
    designs = ["Onshore H2", 
    "Offshore H2"]
    turbine_model = [#"osw_12MW",
    #"osw_15MW", 
    "osw_18MW"
    ]
    storage_types = ["pressure_vessel"]
    days_of_storage = 3
    turbine_in = []
    lcoh_out = []
    lcoe_out = []
    site_in = []
    plant_design_in = [] 
    policy_in = []       
    t1 = time()
    count = 0
    for turbine in turbine_model:
        for (i, site) in enumerate([1]):
            for (j, plant_design) in enumerate([1]):
                for storage in storage_types:
                    for (k, policy) in enumerate([1]):
                        lcoh, lcoe, capex_breakdown, opex_breakdown_annual, pf_lcoh, electrolyzer_physics_results, pf_lcoe, annual_energy_breakdown \
                            = run_simulation(storage_type=storage,days=days_of_storage,save_plots=save_plots, turbine_model=turbine, plant_design_scenario=plant_design, incentive_option=policy, verbose=verbose, show_plots=show_plots, use_profast=use_profast,location=site, output_level=3)
                        
                        lcoh_out.append(lcoh)
                        lcoe_out.append(lcoe*1E3)
                        site_in.append(sites[i])
                        turbine_in.append(turbine)
                        plant_design_in.append(designs[j])
                        policy_in.append(policies[k])
                        count += 1
    t2 = time() 
    print("Runs: ", count)
    print("total time: ", t2-t1)
    print("Time per run: ", (t2-t1)/count)
    
    df = pd.DataFrame.from_dict({"Site": site_in, "Turbine": turbine_in, "Design": plant_design_in, "Policy": policy_in, "LCOH": lcoh_out, "LCOE": lcoe_out})
    df.to_csv("initial_out.csv")
    pprint(df)

    return 0 

# run the stuff
if __name__ == "__main__":
    # run_design_options()
    # run_simulation(verbose=True, show_plots=False, save_plots=True,  use_profast=True, incentive_option=1, plant_design_scenario=1)
    
    # for i in range(1,8):
    #     run_simulation(verbose=True, show_plots=False, save_plots=True, use_profast=True, incentive_option=1, plant_design_scenario=i)

    # # run_sweeps(simulate=True)

    # run_policy_options_storage_types(verbose=False, show_plots=False, save_plots=False,  use_profast=True)

    # run_design_options(verbose=False)

    # # process_design_options()

    # run_policy_storage_design_options()

    # colors = ["#0079C2", "#00A4E4", "#F7A11A", "#FFC423", "#5D9732", "#8CC63F", "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"]
    # colors = ["#0079C2",                         "#FFC423", "#5D9732",            "#5E6A71", "#D1D5D8", "#933C06", "#D9531E"]
    # plot_policy_storage_design_options(colors, normalized=True)

    run_for_greensteel_lcoh()
    #run_storage_options()

