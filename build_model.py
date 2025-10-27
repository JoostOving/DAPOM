from gurobipy import Model, GRB
import pandas as pd


def get_default_parameters() -> dict:
    """
    Returns default parameters for the EMS optimization model.
    """
    return {
        "Xmax": 400.0,     # battery capacity (kWh)
        "Qb_max": 100.0,   # max charge/discharge (kW)
        "Qg_max": 535.0,   # grid power limit (kW)
        "kappa": 1000.0,   # penalty per kWh short of target
        "v_target": 0.8,   # target SoC fraction
        "X0": 0.0          # initial SoC
    }


def validate_data(data: pd.DataFrame) -> None:
    """
    Checks if the input Dataframe contains all required columns.
    """

    required_columns = [
        "Truck",
        "Solar_production_kWh",
        "Energy_consumption_kWh",
        "Price_per_kWh",
    ]
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Missing required column: '{col}' in input data")


def create_decision_variables(model: Model, T: int, Qb_max: float, Qg_max: float, solar) -> dict:
    """
    Add the decision variables to the model and returns them as a dictionary.
    """

    b = model.addVars(T, lb=-Qb_max, ub=Qb_max, name="b")     
    x = model.addVars(T, lb=0, name="x")                      
    g = model.addVars(T, lb=-Qg_max, ub=Qg_max, name="g")      
    a = model.addVars(T, lb=0, ub=solar, name="a")          
    gamma = model.addVar(lb=0, name="gamma")                 

    return {"b": b, "x": x, "g": g, "a": a, "gamma": gamma}


def add_constraints(model: Model, data: pd.DataFrame, vars: dict, params: dict) -> None:
    """
    Add all constraints to the EMS optimization model.
    """

    T = len(data)
    truck = data["Truck"].values
    solar = data["Solar_production_kWh"].values
    load = data["Energy_consumption_kWh"].values

    b, x, g, a, gamma = vars["b"], vars["x"], vars["g"], vars["a"], vars["gamma"]

    # 1. Truck charge/discharge only when connected
    for t in range(T):
        model.addConstr(b[t] <= params["Qb_max"] * truck[t], name=f"charge_limit_{t}")
        model.addConstr(b[t] >= -params["Qb_max"] * truck[t], name=f"discharge_limit_{t}")

    # 2. SoC dynamics, only active when truck is connected
    model.addConstr(x[0] == params["X0"] + b[0] * truck[0], name="soc_start")
    for t in range(1, T):
        if truck[t] == 1: model.addConstr(x[t] == x[t - 1] + b[t], name=f"soc_dyn_{t}")
        else:
            # if the truck is disconnected, SoC is zero
            model.addConstr(x[t] == 0, name=f"soc_reset_{t}")

    # 3. Curtailment limit
    for t in range(T):
        model.addConstr(a[t] <= solar[t], name=f"curtail_{t}")

    # 4. Energy balance
    for t in range(T):
        model.addConstr(
            load[t] + b[t] + a[t] == solar[t] + g[t], name=f"energy_balance_{t}",)

    # 5. Departure SoC target (at end of session)
    model.addConstr(
        x[T - 1] >= params["v_target"] * params["Xmax"] - gamma, name="soc_target",)


def set_objective(model: Model, vars: dict, data: pd.DataFrame, params: dict) -> None:
    """
    Defines the objective function for the EMS optimization model.
    """

    price = data["Price_per_kWh"].values
    g, gamma = vars["g"], vars["gamma"]
    T = len(data)

    objective = sum(price[t] * g[t] for t in range(T)) + params["kappa"] * gamma
    model.setObjective(objective, GRB.MINIMIZE)


def build_model(data: pd.DataFrame, parameters: dict | None = None):
    """
    Builds the full Gurobi EMS model for one charging session. Takes the dataframe as input and puts out the model and relevant info.
    """

    if parameters is None:
        parameters = get_default_parameters()

    validate_data(data)

    model = Model("EMS_Optimization")

    model.Params.OutputFlag = 0 # suppress Gurobi output

    T = len(data)
    vars = create_decision_variables(model, T, parameters["Qb_max"], parameters["Qg_max"], data["Solar_production_kWh"].values)
    add_constraints(model, data, vars, parameters)
    set_objective(model, vars, data, parameters)

    info = {
        "T": T,
        "parameters": parameters,
        "vars": vars
    }

    return model, info
