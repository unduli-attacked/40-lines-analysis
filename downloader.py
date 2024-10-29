import requests
import random
import json
import time
import math

# define static vars
api_base = "https://ch.tetr.io/api"
leaderboard_endpoint = "/records/40l_global" # global 40 lines leaderboard
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


# TODO call this with page size 100 and infinite record limit to get data on the full leaderboard
getLeaderboard(20,10)

# TODO iterate through user list and download summary data as well as individual game records (progression?)