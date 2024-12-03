import pandas as pd
import math
import os

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

def genCompleteSets(leaderboard_file, user_info_file):
    leaderboard = pd.read_csv(leaderboard_file, index_col=[0])
    existing_recs = pd.read_csv(user_info_file, index_col=[0])

    # drop duplicates
    leaderboard_rank = leaderboard["rank"].loc[~leaderboard["rank"].isin(existing_recs["rank"])].tolist()
    print(str(leaderboard_rank[0]))
    splits = [math.floor(len(leaderboard_rank)/3),(math.floor(len(leaderboard_rank)/3)*2),len(leaderboard_rank)]
    print(splits)

    fl_jay = open(set_file+"/jay_rank_sets.csv", "w")
    tmpStr = ""
    for i in range(0,splits[0]):
        tmpStr += str(leaderboard_rank[i])+","
        if (i+1) % 15 == 0:
            fl_jay.write(tmpStr.strip(",")+"\n")
            tmpStr = ""
    fl_jay.close()
    
    fl_joseph = open(set_file+"/joseph_rank_sets.csv", "w")
    tmpStr = ""
    for i in range(splits[0], splits[1]):
        tmpStr += str(leaderboard_rank[i])+","
        if (i+1) % 15 == 0:
            fl_joseph.write(tmpStr.strip(",")+"\n")
            tmpStr = ""
    fl_joseph.close()

    fl_henry = open(set_file+"/henry_rank_sets.csv", "w")
    tmpStr = ""
    for i in range(splits[1], splits[2]):
        tmpStr += str(leaderboard_rank[i])+","
        if (i+1) % 15 == 0:
            fl_henry.write(tmpStr.strip(",")+"\n")
            tmpStr = ""
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

def compileData(out_folder, records=True):
    out_sep = out_folder+"/out_sep"
    user_df = pd.DataFrame()
    if records:
        record_df = pd.DataFrame()
    print("Reading files")
    for filename in os.listdir(out_sep):
        # print("Reading file", filename)
        try:
            if filename.startswith("user_info"):
                # this is a user file
                user_df = pd.concat([user_df, pd.read_csv(out_sep+"/"+filename, index_col=[0])], ignore_index=True)
            elif records and filename.startswith("records"):
                # this is a records file
                record_df = pd.concat([record_df, pd.read_csv(out_sep+"/"+filename, index_col=[0])], ignore_index=True)
        except Exception as e:
            print("Error reading file", filename,":", e)

    print("Files read")
    file_suffix = "_ranks_"+str(user_df["rank"].min())+"-"+str(user_df["rank"].max())+".csv"

    user_df.sort_values(["rank"], ignore_index=True, inplace=True)
    user_fl = open(out_folder+"/compiled_user_info"+file_suffix, "w")
    user_df.to_csv(user_fl, lineterminator="\n")
    
    if records:
        record_df.sort_values(["final_time"], ignore_index=True, inplace=True)
        record_fl = open(out_folder+"/compiled_records"+file_suffix, "w")
        record_df.to_csv(record_fl, lineterminator="\n")

def check_data(out_folder):
    leaderboard_df = pd.DataFrame()
    user_df = pd.DataFrame()
    record_df = pd.DataFrame()
    print("Loading data")
    for filename in os.listdir(out_folder):
        if filename.startswith("user_leaderboard"):
            leaderboard_df = pd.read_csv(out_folder+"/"+ filename, index_col=[0])
            print("Leaderboard loaded")
        # elif filename.startswith("compiled_records"):
        #     record_df = pd.concat([record_df, pd.read_csv(out_folder+"/"+ filename, index_col=[0])], ignore_index=True)
        elif filename.startswith("compiled_user"):
            user_df = pd.concat([user_df, pd.read_csv(out_folder+"/"+ filename, index_col=[0])], ignore_index=True)
    print("Data loaded")
    # remove the ranks henry is still working on
    leaderboard_df = leaderboard_df.loc[leaderboard_df["user_id"].isin(range(699206,849525)) == False]
    # print(user_df["username"].to_list())
    print("Finding missing users")
    missing_users = leaderboard_df['user_name'].loc[leaderboard_df["user_name"].map(lambda x: x not in user_df['username'].values)]
    print("MISSING USERS:",missing_users.to_list())

    print("Finding duplicate users")
    duplicate_users = user_df["username"].loc[user_df.duplicated("id")]
    print("DUPLICATE USERS:", duplicate_users.to_list())

check_data("out")
# genRankSets("out/user_leaderboard_1730705078.csv")
# compileData("out")
# genCompleteSets("out/user_leaderboard_1730705078.csv", "out/compiled_user_info_cohorts_13-353.csv")
