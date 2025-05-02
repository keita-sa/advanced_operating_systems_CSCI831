import pickle
import socket
import threading
import time
import os

# ====================
#  Database List with Fault Tolerance (Persistence)
# ====================
class DBList:
    def __init__(self, filename="db_data.pkl"):
        self.value = []
        self.filename = filename
        self.load()

    def append(self, data):
        self.value.append(data)
        self.save()
        return self.value

    def get(self):
        return self.value

    def save(self):
        try:
            with open(self.filename, "wb") as f:
                pickle.dump(self.value, f)
        except Exception as e:
            print(f"[DB Save Error] {e}")

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "rb") as f:
                    self.value = pickle.load(f)
            except Exception as e:
                print(f"[DB Load Error] {e}")

# ====================
#  Server Implementation with Fault Tolerance
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
        client_socket.settimeout(5)
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
        except socket.timeout:
            print("[Server Error] Client connection timed out.")
        except Exception as e:
            print(f"[Server Error] {e}")
        finally:
            client_socket.close()

    def run(self):
        print(f"[Server] Running on {self.host}:{self.port}")
        while True:
            try:
                client_socket, _ = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except Exception as e:
                print(f"[Server Accept Error] {e}")

# ====================
#  Client Implementation with Retry
# ====================
class Client:
    def __init__(self, server_host="localhost", server_port=5000, retries=3):
        self.server_host = server_host
        self.server_port = server_port
        self.retries = retries

    def append(self, data):
        return self.send_request(("APPEND", data))

    def get(self):
        return self.send_request(("GET", None))

    def send_request(self, request):
        for attempt in range(self.retries):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                    client_socket.settimeout(5)
                    client_socket.connect((self.server_host, self.server_port))
                    client_socket.sendall(pickle.dumps(request))
                    response = client_socket.recv(1024)
                    return pickle.loads(response)
            except (socket.timeout, ConnectionRefusedError) as e:
                print(f"[Client Retry {attempt+1}] {e}")
                time.sleep(1)
            except Exception as e:
                print(f"[Client Error] {e}")
                break
        return "[Client Error] Failed to get response after retries"

# ====================
#  Run
# ====================
if __name__ == "__main__":
    server = Server()
    threading.Thread(target=server.run, daemon=True).start()

    time.sleep(1)

    client = Client()
    print(client.append("Hello"))
    print(client.append("World"))
    print(client.get())
