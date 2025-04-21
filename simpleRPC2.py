import pickle
import socket
import threading

# ====================
#  Database List (Shared Object)
# ====================
class DBList:
    def __init__(self):
        self.value = []

    def append(self, data):
        self.value.append(data)
        return self.value

    def get(self):
        return self.value

# ====================
#  Server Implementation
# ====================
class Server:
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port
        self.db_list = DBList()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024)
            if not data:
                return

            request = pickle.loads(data)

            if request[0] == "APPEND":
                response = self.db_list.append(request[1])
            elif request[0] == "GET":
                response = self.db_list.get()
            else:
                response = f"Unknown command: {request[0]}"

            client_socket.sendall(pickle.dumps(response))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

    def run(self):
        print(f"Server is running on {self.host}:{self.port}...")
        while True:
            client_socket, _ = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

# ====================
#  Client Implementation
# ====================
class Client:
    def __init__(self, server_host="localhost", server_port=5000):
        self.server_host = server_host
        self.server_port = server_port

    def append(self, data):
        return self.send_request(("APPEND", data))

    def get(self):
        return self.send_request(("GET", None))

    def send_request(self, request):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.server_host, self.server_port))
            client_socket.sendall(pickle.dumps(request))
            response = client_socket.recv(1024)
            return pickle.loads(response)

# ====================
#  Testing the RPC Mechanism
# ====================
if __name__ == "__main__":
    server = Server()
    threading.Thread(target=server.run, daemon=True).start()

    client = Client()
    print(client.append("Hello"))     # ['Hello']
    print(client.append("World"))     # ['Hello', 'World']
    print(client.get())               # ['Hello', 'World'] ←  GET request
