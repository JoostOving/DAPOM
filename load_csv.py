import pandas as pd

def get_data_csv():
  pd.read_csv("data.csv")

data = get_data_csv()
print(data)
