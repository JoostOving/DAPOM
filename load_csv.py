import pandas as pd

def get_data_csv():
  
  """Reads data from a CSV file and returns it as a pandas Dataframe."""

  data = pd.read_csv("data.csv")
  return data


