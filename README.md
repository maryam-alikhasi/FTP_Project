# Python Secure FTP Server & Client

This project provides a basic yet secure FTP-like server and client implemented in Python. It supports encrypted communication using TLS/SSL, handles user authentication, and enables a set of standard file and directory operations with a simple permission system.

---

## Key Features

### Secure Communication
- Encrypted control and data channels using TLS/SSL (via Python's `ssl` module).
- Custom SSL certificates (`certificate.crt` and `private.key`) required.

### Client-Server Architecture
- `server.py`: Multi-threaded server handling multiple client connections.
- `client.py`: Command-line interface to interact with the server.

### User Authentication
- `REG <username> <password>` — Register a new user.
- `USER <username>` — Submit username.
- `PASS <password>` — Submit password for authentication.

### File Operations (permission-controlled)
- `LIST [<path>]` — List files (requires `'r'`).
- `RETR <server_path>` — Download file (requires `'r'`).
- `STOR <local> <server>` — Upload file (requires `'w'`).
- `DELE <server_path>` — Delete file (requires `'d'`).

### Directory Operations
- `MKD <server_path>` — Create directory (requires `'c'`).
- `RMD <server_path>` — Remove directory and contents (requires `'d'`).
- `PWD`, `CWD <path>`, `CDUP` — Navigation commands (requires `'r'`).

### Permission Management
- `TRANS <username> <new_permissions>` — Admin command to change another user’s permissions (requires `'t'`).

### Connection Management
- `QUIT` — Gracefully terminate session.

---

## Technical Overview

- **Ports**:
  - Control: `8080`
  - Data: `8081`
- **Threading**: Each client is handled in a separate thread on the server.
- **File Locking**: A shared `file_lock` is used to prevent concurrent access issues.
- **Certificates**: Server requires `certificate.crt` and `private.key`. Client accepts these insecurely (for demo use only).

---

### 1. Start the Server

```bash
python server.py
```

### 2. Start the Client (in another terminal)

```bash
python client.py
```

Use the following commands at the prompt:

---

## Client Commands

### Authentication

* Register: `REG newuser secret123`
* Login:

  * `USER admin`
  * `PASS admin`

### File & Directory Operations

* List files: `LIST` or `LIST /folder`
* Download file: `RETR file.txt`
* Upload file: `STOR local.txt server/path.txt`
* Delete file: `DELE server/file.txt`
* Create directory: `MKD new_folder`
* Remove directory: `RMD old_folder`
* Print current directory: `PWD`
* Change directory: `CWD /projects`
* Go to parent directory: `CDUP`

### Permissions

* Transfer rights: `TRANS user1 rwc`

### End Session

* Quit: `QUIT`

---

##  Default Users

Defined in `server.py`:

| Username | Password | Permissions |
| -------- | -------- | ----------- |
| admin    | admin    | rwcdt       |
| user1    | user1    | rwd         |
| user2    | user2    | rc          |
| user3    | user3    | wcd         |

---

##  File Structure

```
.
├── client.py           # FTP client
├── server.py           # FTP server with TLS and threading
├── certificate.crt     # SSL certificate (generate manually)
```

---

##  Notes & Limitations

* **SSL Security**: Client disables hostname verification (`verify_mode = ssl.CERT_NONE`). Use proper validation in production.
* **Hardcoded Ports**: Server uses ports 8080 (control) and 8081 (data). Update in code if needed.
* **No Data Persistence**: User data is stored in-memory; it resets when the server restarts.
* **Basic FTP Subset**: Supports a simplified command set for educational purposes.
* **Locking Granularity**: File-level locking exists but could be refined for concurrent access in production scenarios.

