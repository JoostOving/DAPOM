from load_csv import get_data_csv
from utils import get_departure_times
from build_model import build_model

def main():
    """
    This file combines all the different files together to create a complete program.
    """
data = get_data_csv()
departures = get_departure_times(data["Truck"])
print("Departure times:", departures)
