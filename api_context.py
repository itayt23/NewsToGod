from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import re
from time import time
import urllib
import webbrowser
import requests 
from datetime import datetime, timedelta
import os
import json
import time
import logging
from dotenv import load_dotenv

load_dotenv("api.env")
API =  os.getenv('ts_api_key')
SECRET = os.getenv('ts_secret')

class Pages:
    @staticmethod
    def getRoot(access_url):
        root = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>API Test</title>
            </head>
            <body>
                <script type="application/javascript">
                    window.location.href= "{access_url}"
                </script>
            </body>
            </html>
                    """.encode('utf-8')
        return root            

    @staticmethod
    def getDone():
        done = """<!DOCTYPE html><html><body><pre>
            Closing localhost server and launching application.

            This page may now be closed.
            </pre></html>""".encode(
                    "utf-8")
        return done            

    @staticmethod
    def getUnknown():
        unknown = "<!DOCTYPE html><html><body><pre>404 - Page not found.</pre></html>".encode(
            "utf-8")
        return unknown


class Token_Info:
    def __init__(self, token_dict = None):
        self.access_token = None
        self.refresh_token = None
        self.expires_in = 0
        self.user_id = None

        if token_dict is not None:
            self.from_dic(token_dict)


    def from_dic(self, dict):
        self.access_token = dict["access_token"]
        self.refresh_token = dict["refresh_token"]
        self.expires_in = int(dict["expires_in"])
        self.user_id = dict["id_token"]


    def to_dict(self):
        res = {
            "access_token" : self.access_token,
            "refresh_token" : self.refresh_token,
            "expires_in" : self.expires_in,
            "userid" : self.user_id
        }
        return res

class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        # Serve root page with sign in link
        if self.path == '/':

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(Pages.getRoot(Context.getAccessUrl()))

            return

        # Check if query path contains case insensitive "code="
        code_match = re.search(r'code=(.+)', self.path, re.I)

        if code_match:

            user_auth_code = code_match[1]
            #global token_access
            token_access = Context.convertAuthCode(user_auth_code)
            Context.TOKENS.from_dic(token_access)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(Pages.getDone())
            # User has logged in - terminate localhost server
            thread = threading.Thread(target=Context.HTTPD.shutdown, daemon=True)
            thread.start()
            time.sleep(2.5) # i added it beacuse sometimes it stuck
            

            return

        # Send 404 error if path is none of the above
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(Pages.getUnknown())

        return



class Context:

    def __init__(self, is_live=False,port=3000, local_url=None):
        if is_live:
            Context.API_BASE_URL = Context.API_LIVE_URL
        else:
            Context.API_BASE_URL = Context.API_LIVE_URL       

        Context.PORT = port
        Context.REDIRECT_URI = f'http://localhost:{str(Context.PORT)}'

        if local_url is not None:
            Context.REDIRECT_URI = local_url


    PATH = 'cache/keys.cache'
    API_KEY = API
    SECRET_KEY = SECRET
    API_SIM_URL = "https://sim-api.tradestation.com/v3"  # Without trailing slash
    API_LIVE_URL = "https://api.tradestation.com/v3"  # Without trailing slash
    API_BASE_URL = None
    PORT = 3000
    REDIRECT_URI = None
    TOKENS = Token_Info()
    HTTPD = None

    #def _initialize(self, on_ready):
    async def _initialize(self):
        server_address = ('', Context.PORT)
        httpd = HTTPServer(server_address, RequestHandler)
        Context.HTTPD = httpd
        print(f'Serving on http://localhost:{str(Context.PORT)}')
        webbrowser.open('http://localhost:3000')
        httpd.serve_forever()
        Context.HTTPD = None

        #on_ready()

    #def initialize(self, on_ready):
    async def initialize(self):
        if os.path.exists(Context.PATH):
            try:
                with open(Context.PATH, 'r') as outfile:
                    data = json.load(outfile)    
                Context.TOKENS.from_dic(data)
                self.refreshAccessToken(True)
                #on_ready()
            except Exception as ex:
                logging.warn(ex)
                #self._initialize(on_ready)
                await self._initialize()
        else:
            #self._initialize(on_ready)    
            await self._initialize()    
            logging.debug("refreshing")
            self.refreshAccessToken()
            logging.debug("done")

    @staticmethod
    def getAccessUrl():

        query_string = urllib.parse.urlencode({
            'redirect_uri': Context.REDIRECT_URI,
            'client_id': Context.API_KEY,
            'response_type': 'code',
            "scope": "openid offline_access MarketData ReadAccount Trade Crypto",
            "audience": "https://api.tradestation.com"
        })

        access_url = f'https://signin.tradestation.com/authorize?{query_string}'
        print('access url', access_url)

        return access_url 

    # Uses authorization code to obtain response containing access token, refresh token, user id,
    # and expriation time
    @staticmethod
    def convertAuthCode(auth_code):

        post_data = {
            'grant_type': 'authorization_code',
            'client_id': Context.API_KEY,
            'client_secret': Context.SECRET_KEY,
            'redirect_uri': Context.REDIRECT_URI,
            'code': auth_code
        }

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_url = 'https://signin.tradestation.com/oauth/token'
        # post_url = f'{Context.API_BASE_URL}/Security/Authorize'
        response = requests.post(post_url, headers=headers, data=post_data)

        if response.status_code != 200:
            raise Exception(
                f"Could not load access and refresh tokens from authorization code")

        return response.json()

    # This method uses the refresh token to obtain a new access token if
    # force_refresh is passed as True or expiration time remaining is less
    # than 20 seconds. self.access_token is updated with the new access token
    def refreshAccessToken(self, force_refresh=False):
        
        expiration = datetime.now() + timedelta(seconds=Context.TOKENS.expires_in)    

        refresh = force_refresh or (expiration - datetime.now()).total_seconds() <= 20

        if refresh:

            # url = Context.API_BASE_URL + "/security/authorize"
            url = 'https://signin.tradestation.com/oauth/token'

            headers = {'content-type': 'application/x-www-form-urlencoded'}
            parameters = {
                'grant_type': 'refresh_token',
                'client_id': Context.API_KEY,
                'redirect_uri': Context.REDIRECT_URI,
                'client_secret': Context.SECRET_KEY,
                'refresh_token': Context.TOKENS.refresh_token
            }

            response = requests.post(url, data=parameters, headers=headers)

            if response.status_code != 200:
                raise Exception("Could not refresh access token")

            data = response.json()
            Context.TOKENS.access_token = data['access_token']
            Context.TOKENS.expires_in = int(data['expires_in'])
            data = Context.TOKENS.to_dict()
            with open(Context.PATH, 'w') as outfile:
                json.dump(data, outfile)

        return Context.TOKENS.access_token

