import pandas as pd

DATETIME = "DateTime"
TRUCK = "Truck"  # δt (0/1)
SOLAR = "Solar_production_kWh"  # St
LOAD = "Energy_consumption_kWh"  # Lt
PRICE = "Price_per_kWh"  # Pt

PARAMETERS = { 
    "Xmax": 400.0,               # battery capacity truck (kWh)
    "Qb_max": 100.0,             # charging power truck (kW)
    "Qg_max": 535.0,             # power from/to grid (kW)
    "X0": 0.0,                   # initial SoC truck (kWh)
    "Yn": 1000.0,                # penalty per kWh short of at departure
    "v_target": 0.80,            # fraction of Xmax target at departure
    "time_horizon_hours": None,  # inferred from data length
    "solver_params": {},         # gurobi parameters dict
}

def get_data_csv():
    return pd.read_csv("data.csv")

data = pd.DataFrame(get_data_csv())

print(data)
