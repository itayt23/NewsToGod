import http.client
import requests
from dotenv import load_dotenv
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
# pip install google-auth-oauthlib


load_dotenv("api.env")
callbacks_urls = ['http://localhost','http://localhost:80','http://localhost:3000','http://localhost:3001','http://localhost:8080',
        'http://localhost:31022']

logout_urls = ['http://localhost/logout','http://localhost:80/logout','http://localhost:3000/logout','http://localhost:3001/logout',
        'http://localhost:8080/logout','http://localhost:31022/logout']

querystring = {
    'response_type':'code',
    'client_id' : os.getenv('ts_api_key'),
    'redirect_uri': 'http://localhost:80',
    'audience': 'https://api.tradestation.com',
    'scope' : 'MarketData'
}  

authorization_url = 'https://signin.tradestation.com/authorize'

conn = http.client.HTTPSConnection("")

payload = "{\"initiate_login_uri\": \"https://signin.tradestation.com/authorize\"}"


conn.request("PATCH", authorization_url, querystring)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

print("bla blab lba lba")




# respone = requests.get(authorization_url,params=querystring)
# auth_code = requests.get(respone.url)
# print(auth_code.url)
# print(auth_code.text)
# print(respone.url)
# print(respone.text)
# print(respone.json())


# flow = InstalledAppFlow.from_client_secrets_file(
#     'client_secrets.json',
#     scopes=['https://www.googleapis.com/auth/cloud-platform'])

# cred = flow.run_local_server(
#     host='localhost',
#     port=8088,
#     authorization_prompt_message='Please visit this URL: {url}',
#     success_message='The auth flow is complete; you may close this window.',
#     open_browser=True)

# with open('refresh.token', 'w+') as f:
#     f.write(cred._refresh_token)

# print('Refresh Token:', cred._refresh_token)
# print('Saved Refresh Token to file: refresh.token')








# from google.oauth2 import service_account

# SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
# SERVICE_ACCOUNT_FILE = '/path/to/service.json'

# credentials = service_account.Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES)



# def make_connection(): # will recive acess token that is valid for 20 minutes
#     authorization_url = 'https://signin.tradestation.com/authorize'
#     querystring = {
#         'response_type':'code',
#         'client_id' : os.getenv('ts_api_key'),
#         'redirect_uri': 'http://localhost',
#         'audience': 'https://api.tradestation.com',
#         'scope' : 'MarketData'
#     }  


# def get_access_token(url, client_id, client_secret):
#     response = requests.get(
#         url,
#         data=querystring
#         # auth=(client_id, client_secret),
#     )
#     # return response.json()["access_token"]
#     print(response.json())
#     return response.json()


# get_access_token(authorization_url, os.getenv('ts_api_key'),os.getenv('ts_secret')) 

    # response = requests.request("POST", url=authorization_url, params=querystring)
    # print(response)
    # data = json.loads(response.text)
    # print(data)

# make_connection()


# myToken = '<token>'
# myUrl = '<website>'
# head = {'Authorization': 'token {}'.format(myToken)}
# response = requests.get(myUrl, headers=head)