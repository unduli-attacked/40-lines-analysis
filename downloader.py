import requests
import random
import json
import time
import math
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

# define static vars
api_base = "https://ch.tetr.io/api"
leaderboard_endpoint = "/records/40l_global" # global 40 lines leaderboard
user_info_endpoint = "/users"
user_records_endpoint = "/records/40l" # APPEND TO USER INFO
speed_limiter = 1 # time to sleep between requests, in seconds
session_id = "CSCI4502_"+str(random.randbytes(16).hex()) # TODO check that this actually works
headers = {"X-Session-ID":session_id}
out_folder = "out_test"


# download the leaderboard
def getLeaderboard(num_records=math.inf, page_size=100):
    # check inputs
    if num_records % page_size != 0:
        print("num_records must be divisible by page_size")
        return None
    if page_size < 1 or page_size > 100:
        print("invalid page size")
        return None
    
    leaderboard_df = pd.DataFrame(columns=["user_id", "user_name", "rank", "final_time", "record_id", "prisecter"])

    # initialize output files
    out_summ_name = out_folder+"/user_leaderboard_"+str(math.floor(time.time()))+".csv"
    
    # prepare to loop
    last_prisecter = ""
    limit = str(page_size)
    rec_count = 0
    fail = False

    # request records until num_records have been returned or the query fails
    while rec_count < num_records and not fail:
        # assemble the request URL
        req_str = api_base+leaderboard_endpoint+"?"
        if last_prisecter:
            # pass in the last prisecter for pagination
            req_str += "after="+last_prisecter+"&"
        req_str+="limit="+limit

        # get page
        resp = requests.get(req_str, headers=headers)

        # get start time for speed limit
        pgStart = time.time()

        respPage = resp.json()

        # check if data was returned
        if respPage["success"] == True and len(respPage["data"]["entries"]) > 0:
            # add returned records to the dataframe

            # iterate through each record on the page
            for i in respPage["data"]["entries"]:
                rec_count += 1

                last_prisecter = str(i["p"]["pri"])+":"+str(i["p"]["sec"])+":"+str(i["p"]["ter"])
                rec_row = {
                    "user_id": i["user"]["id"],
                    "user_name": i["user"]["username"],
                    "rank": rec_count,
                    "final_time": i["results"]["stats"]["finaltime"],
                    "record_id": i["_id"],
                    "prisecter": last_prisecter
                }

                leaderboard_df = pd.concat([leaderboard_df, pd.DataFrame(rec_row, index=[0])], ignore_index=True)
        else:
            # no records were returned, something is wrong or we've hit the bottom
            fail=True

        # record end time
        pgEnd = time.time()

        # determine if the speed limit has been met
        if speed_limiter > (pgEnd - pgStart):
            # speed limit has not been met, sleep for remaining time
            time.sleep(speed_limiter - (pgEnd - pgStart))
    
    # write the leaderboard to a file
    out_summ_fl = open(out_summ_name, "w")
    leaderboard_df.to_csv(out_summ_fl)

def processRecord(record_json, user_id):
    results = record_json["results"]
    # FIXME this is stupid
    record_row = {
        "record_id": record_json["_id"], 
        "user_id": user_id, 
        "datetime": record_json["ts"], 
        "current_pb": record_json["pb"], 
        "ever_pb": record_json["oncepb"], 
        "final_time": results["stats"]["finaltime"], 
        "pps": results["aggregatestats"]["pps"], 
        "inputs": results["stats"]["inputs"], 
        "score": results["stats"]["score"], 
        "pieces_placed": results["stats"]["piecesplaced"], 
        "singles": results["stats"]["clears"]["singles"], 
        "doubles": results["stats"]["clears"]["doubles"], 
        "triples": results["stats"]["clears"]["triples"], 
        "quads": results["stats"]["clears"]["quads"], 
        "all_clears": results["stats"]["clears"]["allclear"], 
        "finesse_faults": results["stats"]["finesse"]["faults"], 
        "finesse_perf": results["stats"]["finesse"]["perfectpieces"]
    }
    # print(record_row)
    return record_row

def getUserRecords(records_df, recent_req, user_id, last_prisecter="", self=None):
    while True:
        req_url = recent_req
        if last_prisecter != "":
            req_url += "&after="+last_prisecter
        
        user_recent = requests.get(req_url, headers=headers)
        pgStart = time.time()

        if user_recent.status_code == 200:
            recent_data = user_recent.json()["data"]["entries"]
            if len(recent_data) < 1:
                return records_df
            for rec in recent_data:
                records_df = pd.concat([records_df, pd.DataFrame(processRecord(rec, user_id), index=[0])], ignore_index=True)
            
            last_prisecter = str(rec["p"]["pri"])+":"+str(rec["p"]["sec"])+":"+str(rec["p"]["ter"])

        pgEnd = time.time()
        # determine if the speed limit has been met
        if speed_limiter > (pgEnd - pgStart):
            # speed limit has not been met, sleep for remaining time
            time.sleep(speed_limiter - (pgEnd - pgStart))

def getUserData(leaderboard_file, rank_list):

    info_df = pd.DataFrame(columns=["id", "username", "rank", "country", "created_date", "xp", "achievement_rating", "TL_games_played", "TL_games_won", "TL_play_time", "num_records"])
    records_df = pd.DataFrame(columns=["record_id", "user_id", "datetime", "current_pb", "ever_pb", "final_time", "pps", "inputs", "score", "pieces_placed", "singles", "doubles", "triples", "quads", "all_clears", "finesse_faults", "finesse_perf"])
    
    leaderboard = pd.read_csv(leaderboard_file, index_col=0)
    # print(leaderboard.info())
    leaderboard = leaderboard.loc[leaderboard["rank"].isin(rank_list)]
    # print(leaderboard.info())
    # leaderboard = leaderboard.loc[leaderboard["rank"] >= best_rank]
    # print(leaderboard.info())

    for i in leaderboard.index:
        row = leaderboard.loc[i]
        print(row)
        info_req = api_base+ user_info_endpoint+"/"+row["user_id"]
        recent_req = info_req+user_records_endpoint+"/recent?limit=100"

        user_info = requests.get(info_req, headers=headers)

        usrStart = time.time()
        
        if user_info.status_code == 200:
            # user info data retrieved
            user_info_data = user_info.json()["data"]
            info_df.loc[len(info_df)] = [user_info_data["_id"], user_info_data["username"], row["rank"], user_info_data["country"], user_info_data["ts"], user_info_data["xp"], user_info_data["ar"], user_info_data["gamesplayed"], user_info_data["gameswon"], user_info_data["gametime"], 0]
            
            # record end time
            usrEnd = time.time()        

            # determine if the speed limit has been met
            if speed_limiter > (usrEnd - usrStart):
                # speed limit has not been met, sleep for remaining time
                time.sleep(speed_limiter - (usrEnd - usrStart))
            
            # get records
            records_df = getUserRecords(records_df, recent_req, row["user_id"])
            
            info_df["num_records"].loc[info_df["id"] == row["user_id"]] = len(records_df["record_id"].loc[records_df["user_id"] == row["user_id"]])
        
        
    file_suffix = "_"+str(min(rank_list))+"-"+str(max(rank_list))+"_"+leaderboard_file.split(".")[0].split("/")[1].split("_")[2]+".csv"
    info_fl = open(out_folder+"/user_info"+file_suffix, "w")
    record_fl = open(out_folder+"/records"+file_suffix, "w")

    info_df.to_csv(info_fl, lineterminator="\n")
    records_df.to_csv(record_fl, lineterminator="\n")


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
    
    fl_henry = open("sets/henry_rank_sets.csv", "w")
    for i in range(0,splits[0]):
        fl_henry.write((','.join(str(j) for j in rank_sets[i])+"\n"))
    fl_henry.close()
    
    fl_joseph = open("sets/joseph_rank_sets.csv", "w")
    for i in range(splits[0], splits[1]):
        fl_joseph.write((','.join(str(j) for j in rank_sets[i])+"\n"))
    fl_joseph.close()

    fl_jay = open("sets/jay_rank_sets.csv", "w")
    for i in range(splits[1], splits[2]):
        fl_jay.write((','.join(str(j) for j in rank_sets[i])+"\n"))
    fl_jay.close()

def downloadMyRankSets(leaderboard_file, name, start_at=1):
    rank_sets = []
    set_fl = open("sets/"+name+"_rank_sets.csv", "r")
    line_count = 0
    for line in set_fl:
        line_count += 1
        if line_count >= start_at:
            rank_sets.append(list(map(lambda x: int(x), line.strip().split(","))))
    set_fl.close()

    for rank_set in rank_sets:
        getUserData(leaderboard_file, rank_set)
    # TODO call getUserData on all sets

# TODO iterate through user list and download summary data as well as individual game records (progression?)
# getUserData("out_test/user_leaderboard_1730666309.csv", 1, 5)

# genRankSets("out_test/user_leaderboard_1730666309.csv")

downloadMyRankSets("out_test/user_leaderboard_1730666309.csv", "jay", 5)