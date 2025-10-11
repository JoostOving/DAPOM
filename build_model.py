from gurobipy import Model, GRB

def build_model(data, parameters=None):
    """
    Builds the Gurobi EMS model for a single charging session.
    """

    # parameters from the assignment
    if parameters is None:
        parameters = {
            "Xmax": 400.0,     # battery capacity (kWh)
            "Qb_max": 100.0,   # max charge/discharge (kW)
            "Qg_max": 535.0,   # grid power limit (kW)
            "Yn": 1000.0,      # penalty per kWh short of target
            "v_target": 0.8,   # target SoC fraction
            "X0": 0.0          # initial SoC
        }

    Xmax = parameters["Xmax"]
    Qb_max = parameters["Qb_max"]
    Qg_max = parameters["Qg_max"]
    kappa = parameters["Yn"]
    nu = parameters["v_target"]
    X0 = parameters["X0"]

    # data from the csv file
    T = len(data)
    truck = data["Truck"].values
    solar = data["Solar_production_kWh"].values
    load = data["Energy_consumption_kWh"].values
    price = data["Price_per_kWh"].values

    model = Model("EMS_Optimization")

    # the decision variables
    b = model.addVars(T, lb=-Qb_max, ub=Qb_max, name="b")
    x = model.addVars(T, lb=0, ub=Xmax, name="x")
    g = model.addVars(T, lb=-Qg_max, ub=Qg_max, name="g")
    a = model.addVars(T, lb=0, ub=solar, name="a")
    gamma = model.addVar(lb=0, name="gamma") 

   
    # Constraints
    # 1. Truck charge/discharge only when connected
    for t in range(T):
        model.addConstr(b[t] <= Qb_max * truck[t], name=f"charge_limit_{t}")
        model.addConstr(b[t] >= -Qb_max * truck[t], name=f"discharge_limit_{t}")

    # 2. SoC dynamics
    model.addConstr(x[0] == X0 + b[0], name="soc_start")
    for t in range(1, T):
        model.addConstr(x[t] == x[t-1] + b[t], name=f"soc_dyn_{t}")

    # 3. Reset SoC when truck is disconnected
    for t in range(T):
        if truck[t] == 0:
            model.addConstr(x[t] == 0, name=f"soc_reset_{t}")

    # 4. Curtailment <= solar production
    for t in range(T):
        model.addConstr(a[t] <= solar[t], name=f"curtail_{t}")

    # 5. Energy balance
    for t in range(T):
        model.addConstr(load[t] + b[t] + a[t] == solar[t] + g[t],
                        name=f"energy_balance_{t}")

    # 6. Departure SoC target for the session (last time period)
    model.addConstr(x[T-1] >= nu * Xmax - gamma, name="soc_target")

    # the objective function
    objective = sum(price[t] * g[t] for t in range(T)) + kappa * gamma
    model.setObjective(objective, GRB.MINIMIZE)

    info = {
        "T": T,
        "parameters": parameters,
        "vars": {"b": b, "x": x, "g": g, "a": a, "gamma": gamma}
    }

    return model, info
