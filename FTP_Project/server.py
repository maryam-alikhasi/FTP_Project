import socket
import ssl
import threading
import os
import datetime
import shutil

# Sample user data (r = read, w = write, c = create, d = delete, t = transfer)
users = {
    'admin': ['admin', 'rwcdt'],
    'user1': ['user1', 'rwd'],
    'user2': ['user2', 'rc'],
    'user3': ['user3', 'wcd'],
}

file_lock = threading.Lock()

class ClientHandler(threading.Thread):
    def __init__(self, control_socket , address):
        super().__init__()
        self.control_socket = control_socket
        self.address = address
        self.username = ''
        self.logged_in = False

    def sign_up(self, request):
        request_parts = request.split()
        if len(request_parts) == 3:
            username = request_parts[1]
            password = request_parts[2]
            if not username or not password:
                self.control_socket.send(b'Username and password cannot be empty\r\n')
                return
            if username in users:
                self.control_socket.send(b'User already exists\r\n')
            else:
                self.username = username
                users[self.username] = [password, 'r']
                self.control_socket.send(b'Registration was successful\r\n')
        else:
            self.control_socket.send(b'Invalid request\r\n')

    def handle_user_request(self, request):
        request_parts = request.split()
        if len(request_parts) == 2:
            self.username = request_parts[1]
            if not self.username:
                self.control_socket.send(b'Username cannot be empty\r\n')
            elif self.username in users:
                self.control_socket.send(b'331 Username accepted, please enter password\r\n')
            else:
                self.control_socket.send(b'530 Invalid login, please try again\r\n')
        else:
            self.control_socket.send(b'Invalid request\r\n')

    def handle_pass_request(self, request):
        request_parts = request.split()
        if len(request_parts) == 2:
            password = request_parts[1]
            if not password:
                self.control_socket.send(b'Password cannot be empty\r\n')
            elif self.username in users and users[self.username][0] == password:
                self.control_socket.send(b'230 Login successful\r\n')
                self.logged_in = True
            else:
                self.control_socket.send(b'530 Invalid password, please try again\r\n')
        else:
            self.control_socket.send(b'Invalid request\r\n')

    def list_files(self, request):
        if self.logged_in:
            request_parts = request.split()
            response = ""
            if 'r' not in users[self.username][1]:
                self.control_socket.send(b'Access denied\r\n')
                return
            if len(request_parts) == 1:
                try:
                    self.control_socket.send(b'125 transfer starting.\r\n')
                    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    data_socket.bind(('127.0.0.1', 8081))
                    data_socket.listen(1)
                    client_data_socket, _ = data_socket.accept()
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    context.load_cert_chain(certfile="certificate.crt", keyfile="private.key")
                    client_data_socket = context.wrap_socket(client_data_socket, server_side=True)
                    file_list = os.listdir('.')
                    for filename in file_list:
                        file_info = os.stat(filename)
                        size = file_info.st_size
                        created_time = datetime.datetime.fromtimestamp(file_info.st_ctime)
                        response += f"{filename} {size} {created_time.strftime('%Y-%m-%d %H:%M:%S')}\r\n"
                    client_data_socket.sendall(response.encode())
                    client_data_socket.close()
                    self.control_socket.send(b'226 Transfer complete.\r\n')
                except Exception as e:
                    self.control_socket.send(b' Error in data connection.\r\n')
            elif len(request_parts) == 2:
                path = request_parts[1]
                try:
                    if not os.path.exists(path) or not os.path.isdir(path):
                        self.control_socket.send(b'Directory does not exist.\r\n')
                        return
                    self.control_socket.send(b'125 transfer starting.\r\n')
                    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    data_socket.bind(('127.0.0.1', 8081))
                    data_socket.listen(1)
                    client_data_socket, _ = data_socket.accept()
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    context.load_cert_chain(certfile="certificate.crt", keyfile="private.key")
                    client_data_socket = context.wrap_socket(client_data_socket, server_side=True)
                    file_list = os.listdir(path)
                    for filename in file_list:
                        full_path = os.path.join(path, filename)
                        file_info = os.stat(full_path)
                        size = file_info.st_size
                        created_time = datetime.datetime.fromtimestamp(file_info.st_ctime)
                        response += f"{filename} {size} {created_time.strftime('%Y-%m-%d %H:%M:%S')}\r\n"
                    client_data_socket.sendall(response.encode())
                    client_data_socket.close()
                    self.control_socket.send(b'226 Transfer complete.\r\n')
                except Exception as e:
                    self.control_socket.send(b'Error in data connection.\r\n')
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'please login first\r\n')

    def retrieve_file(self, request):
        if self.logged_in:
            request_parts = request.split()
            if 'r' not in users[self.username][1]:
                self.control_socket.send(b'Access denied\r\n')
                return
            if len(request_parts) == 2:
                path = request_parts[1]
                if not path :
                    self.control_socket.send(b'Path cannot be empty\r\n')
                    return
                try:
                    with file_lock:
                        if not os.path.isfile(path):
                            self.control_socket.send(b'File not found.\r\n')
                            return
                        self.control_socket.send(b'150 File status okay; about to open data connection.\r\n')
                        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        data_socket.bind(('127.0.0.1', 8081))
                        data_socket.listen(1)
                        client_data_socket, _ = data_socket.accept()
                        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                        context.load_cert_chain(certfile="certificate.crt", keyfile="private.key")
                        client_data_socket = context.wrap_socket(client_data_socket, server_side=True)
                        with open(path, 'rb') as file:
                            while data := file.read(1024): client_data_socket.sendall(data)
                        self.control_socket.send(b'226 Transfer complete.\r\n')
                        client_data_socket.close()
                except Exception as e:
                    self.control_socket.send(b'Error in data connection.\r\n')
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'please login first\r\n')

    def store_file(self, request):
        if self.logged_in:
            request_parts = request.split()
            if 'w' not in users[self.username][1]:
                self.control_socket.send(b'Access denied\r\n')
                return
            if len(request_parts) == 3:
                client_path, server_path = request_parts[1], request_parts[2]
                if not client_path or not server_path :
                    self.control_socket.send(b'Paths cannot be empty\r\n')
                    return
                try:
                    with file_lock:
                        self.control_socket.send(b'150 File status okay, creating data connection.\r\n')
                        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        data_socket.bind(('127.0.0.1', 8081))
                        data_socket.listen(1)
                        client_data_socket, _ = data_socket.accept()
                        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                        context.load_cert_chain(certfile="certificate.crt", keyfile="private.key")
                        client_data_socket = context.wrap_socket(client_data_socket, server_side=True)
                        with open(server_path, 'wb') as file:
                            while data := client_data_socket.recv(1024): file.write(data)
                        client_data_socket.close()
                        self.control_socket.send(b'226 File successfully transferred.\r\n')
                except Exception as e:
                    self.control_socket.send(b'Error in data connection.\r\n')
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def delete_file(self, request):
        if self.logged_in:
            request_parts = request.split()
            if 'd' not in users[self.username][1]:
                self.control_socket.send(b'Access denied\r\n')
                return
            if len(request_parts) == 2:
                server_path = request_parts[1]
                if not server_path:
                    self.control_socket.send(b'Path cannot be empty\r\n')
                    return
                try:
                    with file_lock:
                        if not os.path.isfile(server_path):
                            self.control_socket.send(b'550 File not found or cannot be deleted.\r\n')
                            return
                        os.remove(server_path)
                        self.control_socket.send(b'250 File successfully deleted.\r\n')
                except Exception as e:
                    self.control_socket.send(b'550 File not found or cannot be deleted.\r\n')
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def make_directory(self, request):
        if self.logged_in:
            request_parts = request.split()
            if 'c' not in users[self.username][1]:
                self.control_socket.send(b'Access denied\r\n')
                return
            if len(request_parts) == 2:
                path = request_parts[1]
                if not path:
                    self.control_socket.send(b'Path cannot be empty\r\n')
                    return
                try:
                    if not os.path.exists(path):
                        os.makedirs(path)
                        self.control_socket.send(b'257 New directory created successfully.\r\n')
                    else:
                        self.control_socket.send(b'550 Cannot create directory.\r\n')
                except Exception as e:
                    self.control_socket.send(b'550 Cannot create directory.\r\n')
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def remove_directory(self, request):
        if self.logged_in:
            request_parts = request.split()
            if 'd' not in users[self.username][1]:
                self.control_socket.send(b'Access denied\r\n')
                return
            if len(request_parts) == 2:
                path = request_parts[1]
                if not path:
                    self.control_socket.send(b'Path cannot be empty\r\n')
                    return
                try:
                    if os.path.exists(path) and os.path.isdir(path):
                        shutil.rmtree(path)
                        self.control_socket.send(b'250 Directory successfully removed.\r\n')
                    else:
                        self.control_socket.send(b'550 Directory does not exist or cannot be deleted.\r\n')

                except Exception as e:
                    self.control_socket.send(b'550 Directory does not exist or cannot be deleted.\r\n')
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def print_working_directory(self, request):
        if self.logged_in:
            request_parts = request.split()
            if len(request_parts) == 1:
                try:
                    current_directory = os.getcwd()
                    self.control_socket.send(f'257 "{current_directory}" is the current directory.\r\n'.encode())
                except Exception as e:
                    self.control_socket.send(f'Cannot find current directory.\r\n')
            else:
                self.control_socket.send(f'Invalid request\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def change_working_directory(self, request):
        if self.logged_in:
            request_parts = request.split()
            if 'r' not in users[self.username][1]:
                self.control_socket.send(b'Access denied\r\n')
                return
            if len(request_parts) == 2:
                path = request_parts[1]
                if not path:
                    self.control_socket.send(b'Path cannot be empty\r\n')
                    return
                try:
                    if os.path.exists(path) and os.path.isdir(path):
                        os.chdir(path)
                        self.control_socket.send(b'250 Directory successfully changed.\r\n')
                    else:
                        self.control_socket.send(b'550 Directory does not exist.\r\n')
                except Exception as e:
                    self.control_socket.send(b'Cannot change directory.\r\n')
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def change_to_parent_directory(self, request):
        if self.logged_in:
            request_parts = request.split()
            if 'r' not in users[self.username][1]:
                self.control_socket.send(b'Access denied\r\n')
                return
            if len(request_parts) == 1:
                try:
                    parent_directory = os.path.dirname(os.getcwd())
                    os.chdir(parent_directory)
                    self.control_socket.send(b'250 Changed to parent directory successfully.\r\n')
                except Exception as e:
                    return
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def transfer(self, request):
        if self.logged_in:
            request_parts = request.split()
            if request_parts[1] in users:
                if 't' not in users[self.username][1]:
                    self.control_socket.send(b'Access denied\r\n')
                    return
                if request_parts[1] in users:
                    users[request_parts[1]][1] = request_parts[2]
                    self.control_socket.send(b'Access granted\r\n')
                else:
                    self.control_socket.send(b'Access denied\r\n')
            else:
                self.control_socket.send(b'User doesnt exist\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def quit_connection(self, request):
        if self.logged_in:
            request_parts = request.split()
            if len(request_parts) == 1:
                try:
                    with file_lock:
                        self.control_socket.send(b'221 Connection terminated successfully.\r\n')
                        self.control_socket.close()
                except Exception as e:
                    self.control_socket.send(b'Cannot disconnect.\r\n')
            else:
                self.control_socket.send(b'Invalid request\r\n')
        else:
            self.control_socket.send(b'Please login first\r\n')

    def run(self):
        print(f"-- server connected to {self.address}")
        while True:
            try:
                request = self.control_socket.recv(1024).decode()
                if "REG" in request:
                    self.sign_up(request)
                elif "USER" in request:
                    self.handle_user_request(request)
                elif "PASS" in request:
                    self.handle_pass_request(request)
                elif "LIST" in request:
                    self.list_files(request)
                    continue
                elif "RETR" in request:
                    self.retrieve_file(request)
                    continue
                elif "STOR" in request:
                    self.store_file(request)
                    continue
                elif "DELE" in request:
                    self.delete_file(request)
                    continue
                elif "MKD" in request:
                    self.make_directory(request)
                elif "RMD" in request:
                    self.remove_directory(request)
                elif "PWD" in request:
                    self.print_working_directory(request)
                elif "CWD" in request:
                    self.change_working_directory(request)
                elif "CDUP" in request:
                    self.change_to_parent_directory(request)
                elif "TRANS" in request:
                    self.transfer(request)
                elif "QUIT" in request:
                    self.quit_connection(request)
                    break
                else:
                    response = "HTTP/1.1 400 Bad Request\n\nInvalid request"
                    self.control_socket.sendall(response.encode())

            except Exception as e:
                break

def main():
    host = 'localhost'
    control_port = 8080
    control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="certificate.crt", keyfile="private.key")
    control_socket.bind((host, control_port))
    control_socket.listen(1)
    print(f"Control connection listening on http://{host}:{control_port}")
    while True:
        client_control_socket, client_address = control_socket.accept()
        client_control_socket = context.wrap_socket(client_control_socket, server_side=True)
        client_handler = ClientHandler(client_control_socket, client_address)
        client_handler.start()

if __name__ == '__main__':
    main()