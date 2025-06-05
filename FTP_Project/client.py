import socket
import os
import ssl


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.context.check_hostname = False
        self.context.verify_mode = ssl.CERT_NONE
        self.control_socket = self.context.wrap_socket(self.control_socket, server_hostname = host)
        self.control_socket.connect((self.host, self.port))

    def send_request(self, request):
        self.control_socket.sendall(request.encode())
        return self.control_socket.recv(1024).decode()

    def sign_up(self, request):
        response = self.send_request(request)
        print(f"Received {response!r}")

    def user(self, request):
        response = self.send_request(request)
        print(f"Received {response!r}")

    def Pass(self, password):
        response = self.send_request(password)
        print(f"Received {response!r}")

    def list_files(self , request):
        response = self.send_request(request)
        print(response)
        if "125" in response:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
                data_socket = self.context.wrap_socket(data_socket, server_hostname = self.host)
                data_socket.connect((self.host, 8081))
                data_response = data_socket.recv(4096).decode()
                print(data_response)
            final_response = self.control_socket.recv(1024).decode()
            print(final_response)

    def retrieve_file(self, request):
        order_parts = request.split()
        response = self.send_request(request)
        print(response)
        if "150" in response:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
                data_socket = self.context.wrap_socket(data_socket, server_hostname=self.host)
                data_socket.connect((self.host, 8081))
                filename = os.path.basename(order_parts[1])
                filename = f"copy_of_{filename}"
                with open(filename, 'wb') as file:
                    while data := data_socket.recv(1024): file.write(data)
            final_response = self.control_socket.recv(1024).decode()
            print(final_response)

    def store_file(self, request):
        order_parts = request.split()
        local_path = order_parts[1]
        if not os.path.isfile(local_path):
            print("File not found on client.")
            return
        response = self.send_request(request)
        print(response)
        if "150" in response:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_socket:
                data_socket = self.context.wrap_socket(data_socket, server_hostname=self.host)
                data_socket.connect((self.host, 8081))
                with open(local_path, 'rb') as file:
                    while data := file.read(1024): data_socket.sendall(data)
                data_socket.shutdown(socket.SHUT_WR)  # Ensure all data is sent
            final_response = self.control_socket.recv(1024).decode()
            print(final_response)

    def delete_file(self, request):
        response = self.send_request(request)
        print(response)

    def make_directory(self, request):
        response = self.send_request(request)
        print(response)

    def remove_directory(self, request):
        response = self.send_request(request)
        print(response)

    def pwd(self , request):
        response = self.send_request(request)
        print(response)

    def change_directory(self, request):
        response = self.send_request(request)
        print(response)

    def cdup(self, request):
        response = self.send_request(request)
        print(response)

    def transfer(self, request):
        response = self.send_request(request)
        print(response)

    def quit(self , request):
        response = self.send_request(request)
        print(response)

def main():
    client = Client('127.0.0.1', 8080)
    while True:
        input_line = input()
        parts = input_line.split()
        if parts[0] == 'REG':
            client.sign_up(input_line)
        elif parts[0] == 'USER':
            client.user(input_line)
        elif parts[0] == 'PASS':
            client.Pass(input_line)
        elif parts[0] == 'LIST':
            client.list_files(input_line)
        elif parts[0] == 'RETR':
            client.retrieve_file(input_line)
        elif parts[0] == 'STOR':
            client.store_file(input_line)
        elif parts[0] == 'DELE':
            client.delete_file(input_line)
        elif parts[0] == 'MKD':
            client.make_directory(input_line)
        elif parts[0] == 'RMD':
            client.remove_directory(input_line)
        elif parts[0] == 'PWD':
            client.pwd(input_line)
        elif parts[0] == 'CWD':
            client.change_directory(input_line)
        elif parts[0] == 'CDUP':
            client.cdup(input_line)
        elif parts[0] == 'TRANS':
            client.transfer(input_line)
        elif parts[0] == 'QUIT':
            client.quit(input_line)
            break
        else:
            break

if __name__ == '__main__':
    main()
