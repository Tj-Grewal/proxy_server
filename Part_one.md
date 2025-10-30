# Step One: Determine Requirements

This document specifies the logic for generating each of the five required HTTP status codes in our simple web server. The server supports GET and HEAD methods only and serves files from the web root directory.

---

## 1. Status Code 200: OK

**Method Used:** GET or HEAD

**Part of Request Causing This Status:**  
The request-target (URI path) pointing to a valid, existing file within the web root

**Logic for Generation:**  
The server returns 200 OK when a request successfully passes all validation checks. First, it verifies the HTTP version is 1.1 and the method is GET or HEAD. Then it checks for security issues like path traversal attempts. After resolving the file path, it confirms the file exists within the web root and is readable. If an `If-Modified-Since` header is present and the file hasn't been modified, it returns 304 instead. Otherwise, it reads the file content and returns it with appropriate headers (Content-Type based on file extension, Content-Length, Last-Modified, etc.). For HEAD requests, only headers are sent without the body.

**Test HTTP Request:**
```http
GET /index.html HTTP/1.1
Host: 127.0.0.1:8080
Connection: close

```

**Expected Response:** `HTTP/1.1 200 OK`  
This request successfully retrieves an existing file from the web root.

---

## 2. Status Code 304: Not Modified

**Method Used:** GET or HEAD

**Part of Request Causing This Status:**  
The `If-Modified-Since` header field containing a timestamp

**Logic for Generation:**  
This status code is returned for conditional requests where the client wants to check if a cached resource is still valid. After validating the request and confirming the file exists, the server checks for an `If-Modified-Since` header. If present, it parses the timestamp and compares it to the file's last modification time. When the file hasn't been modified since the specified time (file modification time ≤ header timestamp), the server returns 304 with a Last-Modified header but no message body, allowing the client to use its cached version.

**Test HTTP Request:**
```http
GET /index.html HTTP/1.1
Host: 127.0.0.1:8080
If-Modified-Since: Fri, 31 Dec 2030 23:59:59 GMT
Connection: close

```

**Expected Response:** `HTTP/1.1 304 Not Modified`  
Using a future date ensures the file appears unmodified, triggering the 304 response.

---

## 3. Status Code 403: Forbidden

**Method Used:** GET or HEAD

**Part of Request Causing This Status:**  
The request-target field in the request-line (particularly path traversal patterns like "..") or file system permissions

**Logic for Generation:**  
The server returns 403 Forbidden to protect against unauthorized access in three scenarios:

1. **Path Traversal Attack:** If the request target contains ".." anywhere, the server immediately rejects it to prevent accessing files outside the web root (e.g., `/../secret.txt` or `/../../etc/passwd`).

2. **Path Outside Web Root:** After normalizing the file path, if it resolves to a location outside the designated web root directory, access is denied.

3. **Insufficient Permissions:** If the file exists but lacks read permissions, the server returns 403 rather than exposing the file's existence.

**Test HTTP Requests:**
```http
GET /../secret.txt HTTP/1.1
Host: 127.0.0.1:8080
Connection: close

```

```http
GET /../../etc/passwd HTTP/1.1
Host: 127.0.0.1:8080
Connection: close

```

**Expected Response:** `HTTP/1.1 403 Forbidden`  
These requests contain ".." sequences attempting directory traversal, which is blocked for security.

---

## 4. Status Code 404: Not Found

**Method Used:** GET or HEAD

**Part of Request Causing This Status:**  
The request-target field in the request-line (the path portion pointing to a non-existent resource)

**Logic for Generation:**  
After passing all security validations (HTTP version, method, and path traversal checks), the server resolves the requested path to a file location within the web root. If either the file doesn't exist (`os.path.exists()` returns False) or the path points to something that isn't a file like a directory (`os.path.isfile()` returns False), the server returns 404 Not Found. This indicates the resource simply isn't available at the requested location.

**Test HTTP Requests:**
```http
GET /nonexistent.html HTTP/1.1
Host: 127.0.0.1:8080
Connection: close

```

```http
GET /fake/directory/file.txt HTTP/1.1
Host: 127.0.0.1:8080
Connection: close

```

**Expected Response:** `HTTP/1.1 404 Not Found`  
These requests ask for files that don't exist in the web root directory.

---

## 5. Status Code 505: HTTP Version Not Supported

**Method Used:** Any (GET, HEAD, or others)

**Part of Request Causing This Status:**  
The HTTP-version field in the request-line (the third token after method and request-target)

**Logic for Generation:**  
Our simple server only supports HTTP/1.1. When parsing the request-line, the server extracts the HTTP version field and checks if it equals "HTTP/1.1". If the version is anything else (like HTTP/1.0, HTTP/2.0, or HTTP/0.9), the server returns 505. This can happen in two places: either during parsing where an "Unsupported HTTP version" error is raised and caught by the exception handler, or during request handling where the version check occurs before processing the request.

**Test HTTP Request:**

```http
GET /index.html HTTP/2.0
Host: 127.0.0.1:8080
Connection: close

```

**Expected Response:** `HTTP/1.1 505 HTTP Version Not Supported`  
These requests use HTTP versions other than 1.1, which our server doesn't support.

---


# Step Two: Build Your Minimal Web Server & Test

## (a)



# STEP 3

## (c)
Our TCP server operates on a thread-per-request model (with exception to the main thread which handles socket acceptance). Working in multithreaded code theoretically allows us to add both concurrency and parallelism letting us accept and handle a much larger number of concurrent users than otherwise possible; however implementation details such as Python's global interpreter lock does hamper our efforts as we cannot achieve true parallelism until later versions of Python, where the GIL is removed, is released.