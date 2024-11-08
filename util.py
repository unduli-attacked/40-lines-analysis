import pandas as pd
import math

set_file = "sets"
def genRankSets(leaderboard_file, cohort_size=10):
    rank_sets = []
    leaderboard = pd.read_csv(leaderboard_file, index_col=0)
    leaderboard["time_cohort"] = leaderboard["final_time"].apply(lambda x: math.floor(x/1000))
    
    for cohort_time in leaderboard["time_cohort"].unique():
        # split into cohorts by final time in seconds
        # assuming a maximum time of 5min this should be ~300 cohorts
        cohort_set = leaderboard["rank"].loc[leaderboard["time_cohort"] == cohort_time]
        sample = cohort_set.sample(n=min(cohort_size, len(cohort_set)), random_state=1).to_list()
        sample.sort()
        rank_sets.append(sample)
    
    splits = [math.floor(len(rank_sets)/3),(math.floor(len(rank_sets)/3)*2),len(rank_sets)]
    
    fl_jay = open(set_file+"/jay_rank_sets.csv", "w")
    for i in range(0,splits[0]):
        fl_jay.write((','.join(str(j) for j in rank_sets[i])+"\n"))
    fl_jay.close()
    
    fl_joseph = open(set_file+"/joseph_rank_sets.csv", "w")
    for i in range(splits[0], splits[1]):
        fl_joseph.write((','.join(str(j) for j in rank_sets[i])+"\n"))
    fl_joseph.close()

    fl_henry = open(set_file+"/henry_rank_sets.csv", "w")
    for i in range(splits[1], splits[2]):
        fl_henry.write((','.join(str(j) for j in rank_sets[i])+"\n"))
    fl_henry.close()

def clean_leaderboard(leaderboard_file):
    df = pd.read_csv(leaderboard_file, index_col=[0])
    print(df.head())

    duplicate_users = df.loc[df.duplicated(subset=["user_id"])==True] # get the second occurance of each duplicate user
    print(len(df["user_name"].unique()))
    for dup in duplicate_users.index:
        rank = df.loc[dup, "rank"]
        df["rank"] = df["rank"].apply(lambda x: x if x <= rank else x - 1)
        df.drop(dup, inplace=True)
    
    out_file = open(leaderboard_file.strip('.csv')+"_clean.csv", "w")
    df.to_csv(out_file, lineterminator="\n")
    out_file.close()


genRankSets("out/user_leaderboard_1730705078.csv")

