import socket, time


if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 80


    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip,port))
    server.listen(5)

    while True:
        client, address = server.accept()
        print(f'connected by {address}')

        message = client.recv(1024)
        message = message.decode("utf-8")
        print(message)

        client.close()
