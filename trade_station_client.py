import socket, time
import requests
from dotenv import load_dotenv
import os




client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 80))
while True:
    time.sleep(5)
    data = client_socket.recv(1024)
    if data.lower() == 'q':
        client_socket.close()
        break

    print("RECEIVED: %s" % data)
    data = input("SEND( TYPE q or Q to Quit):")
    client_socket.send(data)
    if data.lower() == 'q':
        client_socket.close()
        break


# querystring = {
#         'response_type':'code',
#         'client_id' : os.getenv('ts_api_key'),
#         'redirect_uri': 'http://localhost:80',
#         'audience': 'https://api.tradestation.com',
#         'scope' : 'MarketData'
#     }   

# authorization_url = 'https://signin.tradestation.com/authorize'
# response = requests.get(authorization_url,params=querystring)
# print(response.url)
# print("#########################")
# print(response.text)


# if __name__ == "__main__":
#     ip = "127.0.0.1"
#     port = 80


#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server.connect((ip,port))