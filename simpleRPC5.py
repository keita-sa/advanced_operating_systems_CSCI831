import pickle
import socket
import threading
import time
import os

# ====================
# DBList + Server Class (same as your original)
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
        with open(self.filename, "wb") as f:
            pickle.dump(self.value, f)

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as f:
                self.value = pickle.load(f)

class Server:
    def __init__(self, host="localhost", port=5000):
        self.db_list = DBList()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(1024)
            request = pickle.loads(data)
            if request[0] == "APPEND":
                response = self.db_list.append(request[1])
            elif request[0] == "GET":
                response = self.db_list.get()
            else:
                response = "Unknown Command"
            client_socket.sendall(pickle.dumps(response))
        except:
            pass
        finally:
            client_socket.close()

    def run(self):
        print("[Server] Running on localhost:5000")
        while True:
            client_socket, _ = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

# ====================
# Client + Throughput Test
# ====================
class Client:
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port

    def append(self, data):
        for _ in range(3):  # retry 3 times
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((self.host, self.port))
                    sock.sendall(pickle.dumps(("APPEND", data)))
                    return pickle.loads(sock.recv(1024))
            except:
                time.sleep(0.1)
        return None

NUM_CLIENTS = 10
REQUESTS_PER_CLIENT = 100

def client_task(cid, results):
    c = Client()
    for i in range(REQUESTS_PER_CLIENT):
        c.append(f"Data-{cid}-{i}")
    results[cid] = REQUESTS_PER_CLIENT

def main():
    if os.path.exists("db_data.pkl"):
        os.remove("db_data.pkl")

    # Start server thread
    server = Server()
    threading.Thread(target=server.run, daemon=True).start()
    time.sleep(1)  # wait for server to boot

    # Run throughput test
    print("[Test] Starting throughput test...")
    threads = []
    results = [0] * NUM_CLIENTS
    start = time.time()

    for i in range(NUM_CLIENTS):
        t = threading.Thread(target=client_task, args=(i, results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end = time.time()
    total = sum(results)
    print(f"[Result] Total Requests: {total}")
    print(f"[Result] Total Time: {end - start:.2f} sec")
    print(f"[Result] Throughput: {total / (end - start):.2f} req/sec")

if __name__ == "__main__":
    main()
