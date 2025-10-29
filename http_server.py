# TODO: See if there is another exception that's more appropriate than RuntimeError

import dataclasses
from typing import Optional, Final, List, Dict
from dataclasses import dataclass
import re
import socket
import os
import sys
import signal
from datetime import datetime, timezone
import threading
from time import time_ns

HTTP_METHODS: Final[List[str]] = ["GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE"]
HTTP_VERSION: Final[str] = "HTTP/1.1"
HOST: Final[str] = "127.0.0.1"  # localhost
PORT: Final[int] = 8080         # Port number
WEB_ROOT: Final[str] = "."      # Current directory
RECV_BUFFER_SIZE: Final[int] = 4096
CACHE_TTL: Final[int] = 30 * 10 ** 9 # Conversion from second to nanoseconds

TOKEN_PATTERN: re.Pattern = re.compile(r"^[!#$%&'*+\-.\^_`|~0-9A-Za-z]+$")
# Could use urllib module, but unsure if allowed due to proxmity to http module
URL_PATTERN: re.Pattern = re.compile(r"http://([\w\-\.]+)")

@dataclass
class HttpMessage:
    """
    Holds common fields for both HTTP requests and responses
    """
    http_version: str
    headers: Dict[str, str]
    body: Optional[str]

    def set_header(self, key: str, value: str) -> None:
        self.headers[key] = value

    def get_header(self, key: str) -> Optional[str]:
        return self.headers.get(key)

@dataclass
class HttpRequest(HttpMessage):
    """
    Holds fields specific to requests
    """
    method: str
    target: str

    def serialize(self) -> str:
        start_line = f"{self.method} {self.target} {self.http_version}"
        field_lines = "\r\n".join(f"{key}: {value}" for key, value in self.headers.items())

        if self.body is not None:
            return f"{start_line}\r\n{field_lines}\r\n\r\n{self.body}"
        else:
            return f"{start_line}\r\n{field_lines}\r\n\r\n"

@dataclass
class HttpProxyCache:
    """
    In-memory HttpResponse caching

    Entries are in the form of HTTP Objects, expiration timestamp, and a date
    - the HTTP Object is a Python string representation
    - the is an expiration represented in nanoseconds since epoch
    - the date is represented in RFC9110 and RFC 9112 Date standard
    """
    entries: Dict[str, tuple[str, int, str]]
    lock: threading.RLock

    def set(self, target: str, object: str, date: Optional[str]) -> None:
        with self.lock:
            if date is not None:
                self.entries[target] = (object, time_ns() + CACHE_TTL, date)
            else:
                self.entries[target] = (object, time_ns() + CACHE_TTL, datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT'))

    def get_object(self, target: str) -> str | None:
        if self.entries[target] is None:
            return None

        return self.entries[target][0]

    def get_expiry_timestamp(self, target: str) -> int | None:
        if self.entries[target] is None:
            return None

        return self.entries[target][1]

    def get_date(self, target: str) -> str | None:
        if self.entries[target] is None:
            return None

        return self.entries[target][2]

    def exists(self, target: str) -> bool:
        return target in self.entries

    def is_valid(self, target: str) -> bool:
        return self.entries[target][1] > time_ns()

# TODO: make this thread-safe
RESPONSE_CACHE: HttpProxyCache = HttpProxyCache(entries={}, lock=threading.RLock())

def parse_request(payload: str) -> HttpRequest:
    # Parse start-line
    start_line, payload = payload.split('\r\n', maxsplit=1)
    start_line_parts = start_line.split(' ')
    if(len(start_line_parts) != 3):
        raise RuntimeError("Malformed request-line")
    
    method, target, version = start_line_parts

    # Parse method per RFC9112: Appendix A. Collected ABNF and RFC9110: Section 5.6.2: Tokens
    if method == "" or TOKEN_PATTERN.match(method) is None:
        raise RuntimeError("Invalid request-line method")

    if method not in HTTP_METHODS:
        raise RuntimeError("Invalid method")

    # TODO: Add HTTP-version validation for HTTP1.1

    # TODO: Add request-target validation

    if not version.startswith("HTTP/"):
        raise RuntimeError("Invalid HTTP version")
    elif version != HTTP_VERSION:
        raise RuntimeError("Unsupported HTTP version")

    # Parse field-lines
    headers = {}
    field, payload = payload.split('\r\n', maxsplit=1)
    while field != "":
        if ":" not in field:
            raise RuntimeError("Malformed header field-line")

        # TODO: Decide on consistency for LF as specified in RFC9112: Section 2.2: 
        # Message Parsing: Although the line terminator for the start-line and fields is the sequence CRLF, 
        # a recipient MAY recognize a single LF as a line terminator and ignore any preceding CR.
        if '\r' in field or '\n' in field:
            raise RuntimeError("Invalid headerfield-line, unexpected CR or LF")

        key, value = field.split(":", maxsplit=1)
        headers[key] = value
        
        field, payload = payload.split('\r\n', maxsplit=1)

    # Parse body (if applicable)

    # TODO: Handle Transfer-Encoding header
    # TODO: Add Content-Length byte validation
    if headers.get("Content-Length") is None:
        return HttpRequest(
            method=method,
            target=target,
            http_version=version,
            headers=headers,
            body=None
        )

    return HttpRequest(
        method=method,
        target=target,
        http_version=version,
        headers=headers,
        body=payload
    )

def create_response(status_code: int, status_message: str, body: str = "", content_type: str = "text/html", extra_headers: Optional[Dict[str, str]] = None) -> str:
    response = f"{HTTP_VERSION} {status_code} {status_message}\r\n"
    
    # Add standard headers
    response += f"Content-Type: {content_type}\r\n"
    response += f"Content-Length: {len(body.encode())}\r\n"
    response += f"Date: {datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}\r\n"
    response += "Server: SimpleHTTPServer/1.0\r\n"
    
    # Add any extra headers
    if extra_headers:
        for key, value in extra_headers.items():
            response += f"{key}: {value}\r\n"
    
    # End headers and add body
    response += "\r\n"
    response += body
    
    return response

def handle_local_target(request: HttpRequest, web_root: str) -> str:
    # Parse the request target and remove query string if present, since it doesn't affect what file we serve
    # This is probably overkill for the project but adding it in for completeness
    target_path = request.target.split('?')[0]

    # Security check: prevent path traversal attacks (403 Forbidden)
    # For attacks like: GET /../../../etc/passwd HTTP/1.1 - leaking the files
    # TODO Any other things we can think of adding here? 
    if ".." in target_path or target_path.startswith("/.."):
        body = "<html><body><h1>403 Forbidden</h1><p>Access denied.</p></body></html>"
        return create_response(403, "Forbidden", body)
    
    # Convert URL path to file system path
    if target_path == "/":
        target_path = "/index.html"
    
    # Remove leading slash and join with web_root
    relative_path = target_path.lstrip('/')
    file_path = os.path.join(os.path.abspath(web_root), relative_path)
    file_path = os.path.normpath(file_path)
    
    # Ensure the resolved path is still within web_root
    # If not within the web_root, we want to stop anyone from accessing other parts of the server 
    # For example:
    #       "C:\Users\John\Desktop\371\test.html" would be valid since the file is within the web root folder
    #       "C:\Users\John\Desktop\secret.txt" would be invalid since the common path is not the web root folder
    web_root_abs = os.path.abspath(web_root)
    if not os.path.commonpath([file_path, web_root_abs]) == web_root_abs:
        body = "<html><body><h1>403 Forbidden</h1><p>Access denied.</p></body></html>"
        return create_response(403, "Forbidden", body)
    
    # Check if file exists (404 Not Found)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        body = "<html><body><h1>404 Not Found</h1><p>The requested resource was not found.</p></body></html>"
        return create_response(404, "Not Found", body)
    
    # Check if file is readable (403 Forbidden)
    if not os.access(file_path, os.R_OK):
        body = "<html><body><h1>403 Forbidden</h1><p>Access denied.</p></body></html>"
        return create_response(403, "Forbidden", body)
    
    # Get file modification time for conditional requests
    file_mtime = os.path.getmtime(file_path)
    file_mtime_str =  datetime.fromtimestamp(file_mtime, tz=timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Check for conditional request (304 Not Modified)
    if_modified_since = request.get_header("If-Modified-Since")
    if if_modified_since:
        try:
            ims_time = datetime.strptime(if_modified_since.strip(), '%a, %d %b %Y %H:%M:%S GMT')
            ims_time = ims_time.replace(tzinfo=timezone.utc)
            file_time = datetime.fromtimestamp(file_mtime, tz=timezone.utc)
            
            # If file hasn't been modified since the specified time
            if file_time <= ims_time:
                return create_response(304, "Not Modified", "", extra_headers={"Last-Modified": file_mtime_str})
        except ValueError:
            # If we can't parse the date, just ignore it and serve the file
            pass
    
    # Read file content (200 OK)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine content type based on file extension
        content_type = "text/html"
        if file_path.endswith('.css'):
            content_type = "text/css"
        elif file_path.endswith('.js'):
            content_type = "application/javascript"
        elif file_path.endswith('.json'):
            content_type = "application/json"
        elif file_path.endswith('.txt'):
            content_type = "text/plain"
        
        # For HEAD requests, don't include body
        body = "" if request.method == "HEAD" else content
        
        return create_response(200, "OK", body, content_type, extra_headers={"Last-Modified": file_mtime_str})
    
    except Exception as e:
        # Internal server error
        body = f"<html><body><h1>500 Internal Server Error</h1><p>{str(e)}</p></body></html>"
        return create_response(500, "Internal Server Error", body)

def handle_remote_target(request: HttpRequest) -> str:
    # Get the remote
    hostname = URL_PATTERN.match(request.target)
    if hostname is None:
        raise RuntimeError()
    hostname = hostname.group(1)

    # The object exists in cache and it's TTL is still valid then return the object as is
    if RESPONSE_CACHE.exists(request.target) and RESPONSE_CACHE.is_valid(request.target):
        cached_object = RESPONSE_CACHE.get_object(request.target)

        if cached_object is not None:
            print(f"Cache hit for target: {request.target}")
            return cached_object

    # The object exists in cache but it's TTL is invalid then add a If-Modified-Since header
    if RESPONSE_CACHE.exists(request.target) and RESPONSE_CACHE.is_valid(request.target) is False:
        cached_date = RESPONSE_CACHE.get_date(request.target)
        if cached_date is not None:
            print(f"Cache TTL invalidated for target: {request.target}")
            request.set_header("If-Modified-Since", cached_date)

    # Otherwise if the object does not exist in cache, send the request as is
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((hostname, 80))
        client_socket.send(request.serialize().encode("utf-8"))

        response = b""

        while True:
            received = client_socket.recv(RECV_BUFFER_SIZE)
            if received == b"":
                break;

            response += received

    # TODO: technical spec violation since all start-lines and field-liens should be USASCII, but UTF-8 is a superset
    response = response.decode("utf-8")

    # Handle cache re-validation, specifically, if on 304, then re-seat the cached_object into the cache again
    if RESPONSE_CACHE.exists(request.target) and RESPONSE_CACHE.is_valid(request.target) is False:
        lines = response.split('\r\n')
        
        start_line = [line for line in lines if line.startswith(HTTP_VERSION)][0]
        version, status_code, status_message = start_line.split(' ', maxsplit=2)

        # Check if 304 Not Modified exists
        if int(status_code) == 304:
            # If true, re-set the cached_object into cache
            last_modified = [line for line in lines if line.startswith("Last-Modified")][0]
            cached_object = RESPONSE_CACHE.get_object(request.target)

            print(status_code)
            print(last_modified)

            if cached_object is not None:
                RESPONSE_CACHE.set(request.target, cached_object, last_modified.split(": ")[1])
                print(f"Cache revalidated for: {request.target}")
                return cached_object

    RESPONSE_CACHE.set(request.target, response, None)
    return response

def handle_request(request: HttpRequest, web_root: str = ".") -> str:
    # Check HTTP version (505 HTTP Version Not Supported)
    if request.http_version != HTTP_VERSION:
        body = "<html><body><h1>505 HTTP Version Not Supported</h1></body></html>"
        return create_response(505, "HTTP Version Not Supported", body)

    # Only support GET and HEAD methods for this simple server
    if request.method not in ["GET", "HEAD"]:
        body = "<html><body><h1>405 Method Not Allowed</h1></body></html>"
        return create_response(405, "Method Not Allowed", body, extra_headers={"Allow": "GET, HEAD"})

    if request.target.startswith("http://"):
        return handle_remote_target(request)
    elif request.target.startswith("https://"):
        # TODO: out of scope for project, requires CONNECT method due to TLS
        # This should be covered in earlier method check, but possible that client is inappropriately using methods
        body = "<html><body><h1>501 Not Implemented</h1></body></html>"
        return create_response(501, "Not Implemented", body)
    else:
        return handle_local_target(request, web_root)

# TODO: find out what the type of client_address is, socket._RetAddress gives AttributeErrors
def handle_connection(client_socket: socket.socket, client_address, web_root: str) -> None:
    print(f"\nConnection from {client_address}")

    try:
        request_data = client_socket.recv(4096).decode('utf-8')

        if not request_data:
            client_socket.close()
            return

        print(f"Request:\n{request_data[:200]}...")  # Print first 200 chars

        try:
            request = parse_request(request_data)
            response = handle_request(request, web_root)

            print(f"Response: {response.split(chr(13))[0]}")  # Print status line

        except RuntimeError as e:
            print(f"Error parsing request: {e}")
            if "Unsupported HTTP version" in str(e):
                body = "<html><body><h1>505 HTTP Version Not Supported</h1></body></html>"
                response = create_response(505, "HTTP Version Not Supported", body)
            else:
                body = f"<html><body><h1>400 Bad Request</h1><p>{str(e)}</p></body></html>"
                response = create_response(400, "Bad Request", body)

        # Send response back to client
        client_socket.sendall(response.encode('utf-8'))

    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()

def run_server(host: str = "127.0.0.1", port: int = 8080, web_root: str = "."):
    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    
    # Listen for incoming connections (max 5 queued connections)
    server_socket.listen(5)
    
    print(f"Server listening on http://{host}:{port}")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            # Hands off socket management to thread
            # NOTE: We shouldn't need to .join() all the threads at the end since the threads are self-terminating (specifically, the lack of loops.)
            incoming_thread = threading.Thread(target=handle_connection, args=(client_socket, client_address, web_root))
            incoming_thread.start()

    except KeyboardInterrupt:
        print("\n\nShutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":    
    run_server(HOST, PORT, WEB_ROOT)
