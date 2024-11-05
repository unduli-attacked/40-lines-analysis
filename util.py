import pandas as pd
import math


def genRankSets(leaderboard_file):
    rank_sets = []
    leaderboard = pd.read_csv(leaderboard_file, index_col=0)
    leaderboard["time_cohort"] = leaderboard["final_time"].apply(lambda x: math.floor(x/100))
    
    for cohort_time in leaderboard["time_cohort"].unique():
        # split into cohorts by final time in seconds
        # assuming a maximum time of 5min this should be ~300 cohorts
        cohort_set = leaderboard["rank"].loc[leaderboard["time_cohort"] == cohort_time]
        rank_sets.append(cohort_set.sample(n=min(10, len(cohort_set))).to_list())
    
    splits = [math.floor(len(rank_sets)/3),(math.floor(len(rank_sets)/3)*2),len(rank_sets)]
    
    fl_jay = open("sets/jay_rank_sets.csv", "w")
    for i in range(0,splits[0]):
        fl_jay.write((','.join(str(j) for j in rank_sets[i])+"\n"))
    fl_jay.close()
    
    fl_joseph = open("sets/joseph_rank_sets.csv", "w")
    for i in range(splits[0], splits[1]):
        fl_joseph.write((','.join(str(j) for j in rank_sets[i])+"\n"))
    fl_joseph.close()

    fl_henry = open("sets/henry_rank_sets.csv", "w")
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