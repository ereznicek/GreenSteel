"""
Python Model of Hydrogen Pressure Vessel

2 Scenarios considered:
Above ground steel tanks
Geologic salt caverns

Capital Cost = (power capacity * $/kW) + (duration * $/kWh) + fixed cost


Assumptions:
"""
import CoolProp.CoolProp as CP
import numpy as np
import math
import matplotlib.pyplot as plt


def pressure_vessel(amount_hydrogen,temperature, pressure):
    """Inputs: amount_hydrogen [kg], temperature [celcius], pressure [bar]
    https://www.sciencedirect.com/science/article/pii/S0360319921005838#tbl2"""

    fluid = 'hydrogen'
    R = 8.314       # Ideal Gas Constant [J/mol/K]
    n = 0.00201588  # Molar mass of hydrogen [kg/mol]
    T_given = temperature + 273.15     #[K]
    P_given = pressure*10**5    #[Pa]

    #Calculate compressibility factor at given temp and pressure
    Z = CP.PropsSI('Z', 'P', P_given, 'T', T_given, fluid) 

    #Calculate volumetric storage density
    v = ((1/n)*Z*R*T_given) / P_given    #[m^3/kg]

    #Calculate required storage volume of hydrogen
    storage_volume = v * amount_hydrogen    #[m^3]
    

    #Compressor Work required
    """Assume 85% compressor efficiency. Initial state of hydrogen is 
    assumed to be 0 Pa and the same temperature after the 
    compression i.e. the input temperature."""

    comp_efficiency = 0.85  #Compressor efficiency

    #Hydrogen's enthalpy before compression [J/kg]
    P_initial = 3e6 #[Pa] Typical outlet pressure of PEM electrolyzer
    h_initial = CP.PropsSI('H','P', P_initial, 'T', T_given, fluid)  #[J/kg]

    #Hydrogen's enthaply after compression [J/kg]   
    h_final = CP.PropsSI('H','P', P_given, 'T', T_given, fluid) #[J/kg]
    

    w = (h_final - h_initial) / comp_efficiency #[J/kg] 

    compressor_work =  (amount_hydrogen * w) / (3.6e6)   #[kWh]

    #Calculate Capex

    #Calculate OPEX
    return storage_volume, compressor_work

pressure_vessel(100,25,300)




