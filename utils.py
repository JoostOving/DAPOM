def get_departure_times(truck_availability):
    
    departures = []
    for i in range(1, len(truck_availability)):
        if truck_availability[i - 1] == 1 and truck_availability[i] == 0:
            departures.append(i - 1)
    return departures

