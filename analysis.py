
import copy
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from build_model import build_model
from utils import get_departure_times


def run_sessions(data: pd.DataFrame, parameters: dict) -> dict:
    """
    Run all sessions for a dataset and return total cost, total gamma, and session metrics.
    """

    departures = get_departure_times(data["Truck"])
    start_session = 0

    total_cost = 0.0
    total_gamma = 0.0
    session_metrics = []

    for dep in departures:
        session_data = data.iloc[start_session:dep + 1].copy()
        model, info = build_model(session_data, parameters=parameters)
        model.optimize()

        objval = model.ObjVal if model.Status == 2 else math.nan
        gamma_val = info["vars"]["gamma"].X if model.Status == 2 else math.nan

        total_cost += objval if not math.isnan(objval) else 0.0
        total_gamma += gamma_val if not math.isnan(gamma_val) else 0.0

        session_metrics.append({
            "session_start": start_session,
            "session_end": dep,
            "objval": objval,
            "gamma": gamma_val
        })

        start_session = dep + 1

    return {
        "total_cost": total_cost,
        "total_gamma": total_gamma,
        "session_metrics": session_metrics
    }


def plot_and_save(x, y_dict, xlabel, ylabel, title, filename):
    """
    Plotting function for the upcoming functions to visualize the results.
    """
    plt.figure()
    for label, y in y_dict.items():
        plt.plot(x, y, label=label)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    print(f"Saved plot to {filename}")


# 1. Solar capacity experiment

def experiment_solar_capacity(data, base_params, multipliers, current_capacity_kW=1500, cost_per_kW=1250):
    """
    Vary solar capacity and compute operational + installation costs.
    Returns results DataFrame.
    """
    results = []

    for m in multipliers:
        session_data = data.copy()
        session_data["Solar_production_kWh"] = data["Solar_production_kWh"] * m

        res = run_sessions(session_data, base_params)

        added_kW = max(0, (m - 1.0) * current_capacity_kW)
        install_cost = added_kW * cost_per_kW
        net_cost = res["total_cost"] + install_cost
        

        results.append({
            "multiplier": m,
            "operational_cost": res["total_cost"],
            "install_cost": install_cost,
            "net_cost": net_cost
        })

    df = pd.DataFrame(results)

    # plots the results
    x = (df["multiplier"] - 1.0) * (current_capacity_kW / 1000.0)  
    plot_and_save(x, 
                  {"Operational cost": df["operational_cost"], "Net cost": df["net_cost"]}, "Added solar capacity (MW)", "Cost (EUR)", "Solar Capacity vs Costs", "solar_capacity_vs_cost.png")

    # find the best multiplier
    best_idx = df["net_cost"].idxmin()
    best = df.loc[best_idx]
    print(f"Best solar multiplier: {best['multiplier']}, add {(best['multiplier']-1)*current_capacity_kW/1000:.2f} MW")

    return df


# 2. Grid capacity experiment

def experiment_grid_capacity(data, base_params, qg_values):
    """
    Vary grid capacity (Qg_max) and compute average SoC miss fraction.
    """
    results = []

    for qg in qg_values:
        params = copy.deepcopy(base_params)
        params["Qg_max"] = qg

        res = run_sessions(data, params)
        session_count = len(res["session_metrics"])
        avg_gamma = res["total_gamma"] / max(1, session_count)
        avg_fraction = avg_gamma / (params["v_target"] * params["Xmax"])
        avg_cost = res["total_cost"] / max(1, session_count)

        results.append({
            "Qg_max": qg,
            "avg_gamma_kWh": avg_gamma,
            "avg_miss_fraction": avg_fraction,
            "avg_cost_per_session": avg_cost
        })
        print(f"Qg_max={qg}: avg_gamma={avg_gamma:.2f} kWh, avg_fraction={avg_fraction:.2%}, avg_cost per session={avg_cost:.2f}")

    df = pd.DataFrame(results)

    plot_and_save(df["Qg_max"], {"Avg fraction missed": df["avg_miss_fraction"]},
                  "Grid capacity (kW)", "Fraction missed", "Grid capacity vs SoC miss", "grid_capacity_vs_miss.png")
    return df


# 3. Truck charging power experiment

def experiment_truck_charge_power(data, base_params, qb_values):
    """
    Vary truck charge power (Qb_max) and compute total operational cost.
    """
    results = []

    for qb in qb_values:
        params = copy.deepcopy(base_params)
        params["Qb_max"] = qb

        res = run_sessions(data, params)
        session_count = max(1, len(res["session_metrics"]))
        avg_cost = res["total_cost"] / session_count

        results.append({"Qb_max": qb, "total_cost": res["total_cost"], "avg_cost_per_session": avg_cost})
        print(f"Qb_max={qb}: total_cost={res['total_cost']:.2f}, avg_cost per session={avg_cost:.2f}")

    df = pd.DataFrame(results)
    plot_and_save(df["Qb_max"], {"Total cost": df["total_cost"]},
                  "Truck charging power (kW)", "Total cost (EUR)", "Charging power vs cost", "charge_power_vs_cost.png")
    return df


# 4. SoC target experiment

def experiment_soc_target(data, base_params, targets):
    """
    Vary SoC target (v_target fraction) and compute total cost and avg gamma.
    """
    results = []

    for v in targets:
        params = copy.deepcopy(base_params)
        params["v_target"] = v

        res = run_sessions(data, params)
        avg_gamma = res["total_gamma"] / max(1, len(res["session_metrics"]))
        avg_cost = res["total_cost"] / max(1, len(res["session_metrics"]))
        results.append({
            "v_target": v,
            "total_cost": res["total_cost"],
            "avg_gamma_kWh": avg_gamma,
            "avg_cost_per_session": avg_cost
        })
        print(f"v_target={v:.2f}: total_cost={res['total_cost']:.2f}, avg_gamma={avg_gamma:.2f} kWh, avg_cost per session={avg_cost:.2f}")

    df = pd.DataFrame(results)
    plot_and_save(df["v_target"], {"Total cost": df["total_cost"]},
                  "SoC target fraction", "Total cost (EUR)", "SoC target vs cost", "soc_target_vs_cost.png")
    return df

