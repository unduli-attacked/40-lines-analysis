#%%

import pandas as pd
import os
import seaborn
from datetime import datetime
import time
import math
import matplotlib.pyplot as plt

def pull_pbs():
    print("a")

def load_data(file1, file2=None):
    record_df = pd.read_csv(file1, index_col=[0])
    if file2:
        record_df = pd.concat([record_df, pd.read_csv(file2, index_col=[0])], ignore_index=True)
    
    # construct more attributes
    record_df["kps"] = record_df["inputs"] / record_df["final_time"] # keys per second
    record_df["kpp"] = record_df["inputs"] / record_df["pieces_placed"] # keys per piece
    record_df["percent_perf"] = record_df["finesse_perf"] / record_df["pieces_placed"] # percent of pieces placed with perfect finesse
    # TODO figure out how the finesse percentage is calcualted

    crazy_outlier = record_df.loc[record_df["finesse_faults"] > 8000].index
    record_df.drop(crazy_outlier, inplace=True)

    return record_df

 # %%
record_df = load_data("out/all_records_pt_1.csv", "out/all_records_pt_2.csv")
# record_df = record_df.loc[record_df["current_pb"] == True]
record_df["final_time"] = record_df["final_time"].apply(lambda x: x//1000)

# %%
def hist(record_df):
    # record_df["final_time"] = record_df["final_time"].apply(lambda x: x/1000)
    
    plt.hist(record_df["final_time"], bins=range(13, 353))
    plt.show()
hist(record_df)
# %%
for i in range(110, 130):
    print(len(record_df.loc[record_df["final_time"] == i]))
# %%
