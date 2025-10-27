from load_csv import get_data_csv
from utils import get_departure_times
from build_model import build_model


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


def main():
    """
    Loads the input data, identifies charging sessions, runs the EMS model for each session, and returns all optimization results.
    """

    data = get_data_csv()                   # 1. load the data
    results = run_all_sessions(data)        # 2. run all the sessions
    print(f"Total sessions optimized: {len(results)}")  # 3. report the results
    return results


if __name__ == "__main__":
    results = main()
