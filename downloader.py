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
out_folder = "out"


# download the leaderboard
def getLeaderboard(num_records=math.inf, page_size=100):
    # check inputs
    # if num_records % page_size != 0:
    #     print("num_records must be divisible by page_size")
    #     return None
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
            if rec_count % 10000 == 0:
                # make a backup every 10k records
                out_summ_fl = open(out_summ_name, "w")
                leaderboard_df.to_csv(out_summ_fl, lineterminator="\n")
                out_summ_fl.close() 
                print(rec_count, "records, last prisecter", last_prisecter)
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
    leaderboard_df.to_csv(out_summ_fl, lineterminator="\n")
    out_summ_fl.close()

def processRecord(record_json, user_id):
    try:
        results = record_json["results"]
        record_row = {
            "record_id": record_json["_id"], 
            "user_id": user_id, 
            "datetime": record_json.get("ts", None), 
            "current_pb": record_json.get("pb", False), 
            "once_pb": record_json.get("oncepb", False), 
            "final_time": results.get("stats", {}).get("finaltime", math.nan), 
            "pps": results.get("aggregatestats", {}).get("pps", math.nan), 
            "inputs": results.get("stats", {}).get("inputs", math.nan), 
            "score": results.get("stats", {}).get("score", math.nan), 
            "pieces_placed": results.get("stats", {}).get("piecesplaced", math.nan), 
            "singles": results.get("stats", {}).get("clears", {}).get("singles", math.nan), 
            "doubles": results.get("stats", {}).get("clears", {}).get("doubles", math.nan), 
            "triples": results.get("stats", {}).get("clears", {}).get("triples", math.nan), 
            "quads": results.get("stats", {}).get("clears", {}).get("quads", math.nan), 
            "all_clears": results.get("stats", {}).get("clears", {}).get("allclear", math.nan), 
            "finesse_faults": results.get("stats", {}).get("finesse", {}).get("faults", math.nan), 
            "finesse_perf": results.get("stats", {}).get("finesse", {}).get("perfectpieces", math.nan)
        }
        # print(record_row)
        return record_row
    except Exception as e:
        print("Failed to retrieve record for", user_id,". Error:", e)
        return None

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
                ret_rec = processRecord(rec, user_id)
                if ret_rec:
                    records_df = pd.concat([records_df, pd.DataFrame(ret_rec, index=[0])], ignore_index=True)
            
            last_prisecter = str(rec["p"]["pri"])+":"+str(rec["p"]["sec"])+":"+str(rec["p"]["ter"])

        pgEnd = time.time()
        # determine if the speed limit has been met
        if speed_limiter > (pgEnd - pgStart):
            # speed limit has not been met, sleep for remaining time
            time.sleep(speed_limiter - (pgEnd - pgStart))

def getUserData(leaderboard_file, rank_list):

    info_df = pd.DataFrame(columns=["id", "username", "rank", "cohort", "best_time", "best_record", "country", "created_date", "xp", "achievement_rating", "TL_games_played", "TL_games_won", "TL_play_time", "num_records"])
    records_df = pd.DataFrame(columns=["record_id", "user_id", "datetime", "current_pb", "once_pb", "final_time", "pps", "inputs", "score", "pieces_placed", "singles", "doubles", "triples", "quads", "all_clears", "finesse_faults", "finesse_perf"])
    
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
            try:
                user_info_data = user_info.json()["data"]
                info_df.loc[len(info_df)] = {
                    "id": user_info_data["_id"], 
                    "username": user_info_data.get("username", None), 
                    "rank": row["rank"], 
                    "cohort": math.floor(row["final_time"]/1000),
                    "best_time": row["final_time"],
                    "best_record": row["record_id"],
                    "country": user_info_data.get("country", None), 
                    "created_date": user_info_data.get("ts", None), 
                    "xp": user_info_data.get("xp", math.nan), 
                    "achievement_rating": user_info_data.get("ar", math.nan), 
                    "TL_games_played": user_info_data.get("gamesplayed", math.nan), 
                    "TL_games_won": user_info_data.get("gameswon", math.nan), 
                    "TL_play_time": user_info_data.get("gametime", math.nan), 
                    "num_records": 0
                }
            except Exception as e:
                print("Failed to retrieve user at rank", row["rank"],". Error:", e)
                continue # skip retrieving records for this user
            
            # record end time
            usrEnd = time.time()        

            # determine if the speed limit has been met
            if speed_limiter > (usrEnd - usrStart):
                # speed limit has not been met, sleep for remaining time
                time.sleep(speed_limiter - (usrEnd - usrStart))
            
            # get records
            records_df = getUserRecords(records_df, recent_req, row["user_id"])
            
            info_df["num_records"].loc[info_df["id"] == row["user_id"]] = len(records_df["record_id"].loc[records_df["user_id"] == row["user_id"]])
    cohort = math.floor(row["final_time"]/1000)
        
    file_suffix = "_cohort-"+str(cohort)+"_"+leaderboard_file.split(".")[0].split("/")[1].split("_")[2]+".csv"
    info_fl = open(out_folder+"/user_info"+file_suffix, "w")
    record_fl = open(out_folder+"/records"+file_suffix, "w")

    info_df.to_csv(info_fl, lineterminator="\n")
    records_df.to_csv(record_fl, lineterminator="\n")


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



downloadMyRankSets(leaderboard_file="out/user_leaderboard_1730705078.csv", name="henry")
# getUserData("out_test/user_leaderboard_1730666309_clean.csv", [9,10,11])