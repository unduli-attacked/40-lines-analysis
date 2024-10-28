import requests

api_base = "https://ch.tetr.io/api/"
speed_limiter = 1 # time to sleep between requests, in seconds

# TODO use an X-Session-ID to properly paginate

# TODO get list of users to download via the leaderboard endpoint

# TODO iterate through user list and download summary data as well as individual game records (progression?)