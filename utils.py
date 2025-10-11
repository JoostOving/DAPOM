def get_departure_times(truck_availability):
    """
    Returns a list of departure times based on truck availability data. When the truck is there (1)
    and then not there (0), it indicates a departure.
    """
    departures = []
    for i in range(1, len(truck_availability)):
        if truck_availability.iloc[i - 1] == 1 and truck_availability.iloc[i] == 0:
            departures.append(i - 1)

    # handle last period if truck still connected
    if truck_availability.iloc[-1] == 1:
        departures.append(len(truck_availability) - 1)

    return departures
