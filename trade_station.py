import requests
from dotenv import load_dotenv
import os
import json

load_dotenv("api.env")




def make_connection(): # will recive acess token that is valid for 20 minutes
    authorization_url = 'https://signin.tradestation.com/authorize'
    querystring = {
        'response_type':'code',
        'client_id' : os.getenv('ts_api_key'),
        # 'redirect_uri': 'https://exampleclientapp/callback',
        'audience': 'https://api.tradestation.com',
        'scope' : 'MarketData'
    }   

    response = requests.request("POST", url=authorization_url, params=querystring)
    print(response)
    # data = json.loads(response.text)
    # print(data)

make_connection()