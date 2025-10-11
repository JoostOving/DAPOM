from load_csv import get_data_csv
from utils import get_departure_times
from build_model import build_model

def main():
    """
    Main function to run the EMS optimization for all charging sessions in the data.
    """
    data = get_data_csv()
    departures = get_departure_times(data["Truck"])
    all_results = []

    start_idx = 0
    for t_dep in departures:
        session_data = data.iloc[start_idx:t_dep+1]  
        model, info = build_model(session_data)
        model.optimize()
        
        all_results.append({
            "session_start": start_idx,
            "session_end": t_dep,
            "model": model,
            "info": info
        })

        start_idx = t_dep + 1 

    print(f"Total sessions optimized: {len(all_results)}")

    
    return all_results

if __name__ == "__main__":
    results = main()





