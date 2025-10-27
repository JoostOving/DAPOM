from load_csv import get_data_csv
from utils import get_departure_times
from build_model import build_model, get_default_parameters
from analysis import experiment_solar_capacity, experiment_grid_capacity, experiment_truck_charge_power, experiment_soc_target


def optimize_session(session_data):
    """
    The function builds and optimizes the EMS model for a single charging session.
    """
    model, info = build_model(session_data)
    model.optimize()

    return {
        "model": model,
        "info": info
    }


def run_all_sessions(data):
    """
    Function splits full dataset into sessions and runs optimization for each. It takes the full dataset with all sessions and returns a list of results for each optimized session.
    """
    departures = get_departure_times(data["Truck"])
    all_results = []

    start_session = 0
    for time_dep in departures:
        # extract the current session
        session_data = data.iloc[start_session:time_dep + 1]
        # optimize this session
        result = optimize_session(session_data)
        # add metadata 
        result["session_start"] = start_session
        result["session_end"] = time_dep
        all_results.append(result)

        # update the start for the next session
        start_session = time_dep + 1

    return all_results

def run_analysis(data):
    """
    Runs the four analysis experiments and plots the  results.
    """
    base_params = get_default_parameters()

    print("\n--- Solar Capacity Experiment ---")
    solar_multipliers = [0.5, 0.75, 1.0, 1.25, 1.5]
    experiment_solar_capacity(data, base_params, solar_multipliers)

    print("\n--- Grid Capacity Experiment ---")
    qg_values = [100, 250, 500, 750, 1000]
    experiment_grid_capacity(data, base_params, qg_values)

    print("\n--- Truck Charging Power Experiment ---")
    qb_values = [20, 50, 75, 100, 125]
    experiment_truck_charge_power(data, base_params, qb_values)

    print("\n--- SoC Target Experiment ---")
    soc_targets = [0.6, 0.7, 0.8, 0.9, 1.0]
    experiment_soc_target(data, base_params, soc_targets)


def main():
    """
    Loads the input data, identifies charging sessions, runs the EMS model for each session, and returns all optimization results.
    """

    data = get_data_csv()                   # 1. load the data
    results = run_all_sessions(data)        # 2. run all the sessions
    print(f"Total sessions optimized: {len(results)}")  # 3. report the results

    run_analysis(data)                      # 4. run the analysis 
    return results


if __name__ == "__main__":
    results = main()
