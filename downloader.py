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

def getLeaderboard(num_records, page_size=100):
    session_id = "CSCI4502_"+str(random.randbytes(16).hex()) # TODO check that this actually works
    headers = {"X-Session-ID":session_id}
    
    # check inputs
    if num_records % page_size != 0:
        print("num_records must be divisible by page_size")
        return None
    if page_size < 1 or page_size > 100:
        print("invalid page size")
        return None
    
    # initialize output files
    out_summ_name = "out/user_leaderboard_"+str(math.floor(time.time()))+".csv"
    out_all_name = "out/full_leaderboard_"+str(math.floor(time.time()))+".json"

    out_summ = open(out_summ_name, "w")
    out_summ.write("user_id,user_name,rank,final_time,record_id,pri,sec,ter\n") # CSV header
    out_summ.close()

    out_all = open(out_all_name, "w")
    out_all.write("[\n") # start of JSON array
    out_all.close()
    
    # prepare to loop
    last_prisecter = {}
    rec_count = 0
    fail = False

    # request records until num_records have been returned or the query fails
    while rec_count < num_records and not fail:
        # assemble the request URL
        req_str = api_base+leaderboard_endpoint+"?"
        if last_prisecter:
            # pass in the last prisecter for pagination
            req_str += "after="+last_prisecter+"&"
        req_str+="limit="+str(page_size)

        # get page
        resp = requests.get(req_str, headers=headers)
        respPage = resp.json()

        # get start time for speed limit
        pgStart = time.time()

        # check if data was returned
        if respPage["success"] == True:
            # assemble the summary from the returned data
            summStr = ""
            
            # iterate through each record on the page
            for i in respPage["data"]["entries"]:
                rec_count+=1 # inc record count

                # assemble the summary string for the CSV
                # yes it probably would've been smart to use pandas for this but by the time I thought of that I was committed
                summStr += i["user"]["id"]+","+i["user"]["username"]+","+str(rec_count)+","+str(i["results"]["stats"]["finaltime"])+","+i["_id"]+","+str(i["p"]["pri"])+","+str(i["p"]["sec"])+","+str(i["p"]["ter"])+"\n"
                
                # check if this is the last record on the page
                if rec_count % page_size == 0:
                    # record the prisecter of the last record for the next query
                    # it needs to be in the format pri:sec:ter or it'll throw an error
                    last_prisecter = str(i["p"]["pri"])+":"+str(i["p"]["sec"])+":"+str(i["p"]["ter"])
            
            # write summary data
            try:
                summFl = open(out_summ_name, "a")
                summFl.write(summStr)
                summFl.close()
            except:
                print("summary write error")

            # write full data (json)
            try:
                fullFl = open(out_all_name, "a+")
                fullStr = json.dumps(respPage["data"]["entries"]) # get the entries array
                fullStr = fullStr.strip('[]') # remove the brackets to make a frankenarray
                fullFl.write(fullStr) # write to file
                fullFl.write(",") # add comma
                fullFl.close()
            except:
                print("full write error")
        else:
            # no records were returned, something is wrong or we've hit the bottom
            fail=True

        # record end time
        pgEnd = time.time()

        # determine if the speed limit has been met
        if speed_limiter > (pgEnd - pgStart):
            # speed limit has not been met, sleep for remaining time
            time.sleep(speed_limiter - (pgEnd - pgStart))

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


def getUserData(leaderboard_file, best_rank, worst_rank):
    session_id = "CSCI4502_"+str(random.randbytes(16).hex()) # TODO check that this actually works
    headers = {"X-Session-ID":session_id}

    info_df = pd.DataFrame(columns=["id", "username", "rank", "country", "created_date", "xp", "achievement_rating", "TL_games_played", "TL_games_won", "TL_play_time", "records_progression", "records_recent"])
    records_df = pd.DataFrame(columns=["record_id", "user_id", "datetime", "current_pb", "ever_pb", "final_time", "pps", "inputs", "score", "pieces_placed", "singles", "doubles", "triples", "quads", "all_clears", "finesse_faults", "finesse_perf"])
    
    leaderboard = pd.read_csv(leaderboard_file)
    # print(leaderboard.info())
    leaderboard = leaderboard.loc[leaderboard["rank"] <= worst_rank]
    # print(leaderboard.info())
    leaderboard = leaderboard.loc[leaderboard["rank"] >= best_rank]
    # print(leaderboard.info())

    for i in leaderboard.index:
        row = leaderboard.loc[i]
        # print(row)
        info_req = api_base+ user_info_endpoint+"/"+row["user_id"]
        prog_req = info_req+user_records_endpoint+"/progression"
        recent_req = info_req+user_records_endpoint+"/recent"

        user_info = requests.get(info_req)
        user_prog = requests.get(prog_req)
        user_recent = requests.get(recent_req)

        usrStart = time.time()
        
        if (user_info.status_code == 200):
            # user info data retrieved
            user_info_data = user_info.json()["data"]
            info_df.loc[len(info_df)] = [user_info_data["_id"], user_info_data["username"], row["rank"], user_info_data["country"], user_info_data["ts"], user_info_data["xp"], user_info_data["ar"], user_info_data["gamesplayed"], user_info_data["gameswon"], user_info_data["gametime"], None, None]

            if user_prog.status_code == 200:
                # user progression data retrieved
                prog_data = user_prog.json()["data"]["entries"]

                prog_recs = []
                for rec in prog_data:
                    records_df = pd.concat([records_df, pd.DataFrame(processRecord(rec, row["user_id"]), index=[0])], ignore_index=True)
                    prog_recs.append(rec["_id"])
                # print(info_df.at[i, "records_progression"])
                info_df.at[i, "records_progression"] = prog_recs
            
            if user_recent.status_code == 200:
                recent_data = user_recent.json()["data"]["entries"]

                recent_recs = []
                for rec in recent_data:
                    records_df = pd.concat([records_df, pd.DataFrame(processRecord(rec, row["user_id"]), index=[0])], ignore_index=True)
                    recent_recs.append(rec["_id"])
                info_df.at[i, "records_recent"] = recent_recs
        
        
        # record end time
        usrEnd = time.time()        

        # determine if the speed limit has been met
        if speed_limiter*3 > (usrEnd - usrStart):
            # speed limit has not been met, sleep for remaining time
            time.sleep(speed_limiter*3 - (usrEnd - usrStart))
    file_suffix = "_"+str(best_rank)+"-"+str(worst_rank)+"_"+leaderboard_file.split(".")[0].split("_")[2]+".csv"
    info_fl = open("out/user_info"+file_suffix, "w")
    record_fl = open("out/records"+file_suffix, "w")

    info_df.to_csv(info_fl)
    records_df.to_csv(record_fl)

        


# TODO call this with page size 100 and infinite record limit to get data on the full leaderboard
# getLeaderboard(20,10)

# TODO iterate through user list and download summary data as well as individual game records (progression?)
getUserData("out/user_leaderboard_1730174943.csv", 1, 10)