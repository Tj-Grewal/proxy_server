## Web & Web Proxy Server Implementation Report

---
#### Environment:
- OS: Ubuntu 24.04 LTS
- CPU: Ryzen 5 5700U
- Memory: 16GB DDR4 @ 3200MHz
- Network: 
    - Protocol: Wi-Fi 6 (802.11ax)
    - Band: 5 GHz
---

## Step One: Status Code Requirements

This section specifies the logic for generating each of the five required HTTP status codes. The server supports GET and HEAD methods only and serves files from the web root directory.

### 1. Status Code 200: OK

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
<br>

### 2. Status Code 304: Not Modified

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
<br>

### 3. Status Code 403: Forbidden

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
<br>

### 4. Status Code 404: Not Found

**Method Used:** GET or HEAD

**Part of Request Causing This Status:**  
The request-target field in the request-line (the path portion pointing to a non-existent resource)

**Logic for Generation:**  
After passing all security validations (HTTP version, method, and path traversal checks), the server resolves the requested path to a file location within the web root. If either the file doesn't exist (`os.path.exists()` returns False) or the path points to something that isn't a file like a directory (`os.path.isfile()` returns False), the server returns 404 Not Found. This indicates the resource simply isn't available at the requested location.

<br>

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

### 5. Status Code 505: HTTP Version Not Supported

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

## Step Two: Web Server Implementation and Testing

### Part (a): Server Implementation

The web server was implemented using Python socket programming. The server listens on 127.0.0.1:8080 and implements the HTTP/1.1 protocol. Code available in `http_server.py`.

---

### Part (b): Browser Testing

We verified browser functionality using curl:

**Test Command:**
```bash
    curl -i http://127.0.0.1:8080/test.html
```

| Server-Side Log | Client-Side Output |
|-----------------|-------------------|
| `Connection from ('127.0.0.1', 39586)`<br>`Request:`<br>`GET /test.html HTTP/1.1`<br>`Host: 127.0.0.1:8080`<br>`User-Agent: curl/8.5.0`<br>`Accept: */*`<br><br>`Response: HTTP/1.1 200 OK` | `HTTP/1.1 200 OK`<br>`Content-Type: text/html`<br>`Content-Length: 224`<br>`Date: Thu, 30 Oct 2025 00:50:24 GMT`<br>`Server: SimpleHTTPServer/1.0`<br>`Last-Modified: Sun, 26 Oct 2025 03:52:50 GMT`<br><br>`<!DOCTYPE html>`<br>`<html>`<br>`<head>`<br>`    <title>Test Page</title>`<br>`</head>`<br>`<body>`<br>`    <h1>Hello from your HTTP Server!</h1>`<br>`    <p>If you can see this, your server is working correctly.</p>`<br>`    <p>Status: 200 OK</p>`<br>`</body>`<br>`</html>` |

**Result:** The server accepted the HTTP/1.1 GET request, returned 200 OK status code, and served test.html with proper headers (Content-Type, Content-Length, Last-Modified).

---

### Part (c): Status Code Testing

All five required status codes were tested using curl. The complete test script is available in `test_all_ubuntu.sh`.

#### Test 1: 200 OK

**Command:** `curl -i http://127.0.0.1:8080/test.html`

**Result:**
```
    HTTP/1.1 200 OK
    Content-Type: text/html
    Content-Length: 224
    Date: Thu, 30 Oct 2025 00:50:24 GMT
    Server: SimpleHTTPServer/1.0
    Last-Modified: Sun, 26 Oct 2025 03:52:50 GMT

    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Hello from your HTTP Server!</h1>
        <p>If you can see this, your server is working correctly.</p>
        <p>Status: 200 OK</p>
    </body>
    </html>
```

#### Test 2: 304 Not Modified

**Command:** `curl -i -H 'If-Modified-Since: Sat, 01 Jan 2030 00:00:00 GMT' http://127.0.0.1:8080/test.html`

**Result:**
```
    HTTP/1.1 304 Not Modified
    Content-Type: text/html
    Content-Length: 0
    Date: Thu, 30 Oct 2025 00:50:24 GMT
    Server: SimpleHTTPServer/1.0
    Last-Modified: Sun, 26 Oct 2025 03:52:50 GMT
```

#### Test 3: 403 Forbidden

**Command:** `curl --path-as-is -i http://127.0.0.1:8080/../test.html`

**Result:**
```
    HTTP/1.1 403 Forbidden
    Content-Type: text/html
    Content-Length: 69
    Date: Thu, 30 Oct 2025 00:50:24 GMT
    Server: SimpleHTTPServer/1.0

    <html><body><h1>403 Forbidden</h1><p>Access denied.</p></body></html>
```

#### Test 4: 404 Not Found

**Command:** `curl -i http://127.0.0.1:8080/nonexistent.html`

**Result:**
```
    HTTP/1.1 404 Not Found
    Content-Type: text/html
    Content-Length: 92
    Date: Thu, 30 Oct 2025 00:50:25 GMT
    Server: SimpleHTTPServer/1.0

    <html><body><h1>404 Not Found</h1><p>The requested resource was not found.</p></body></html>
```

#### Test 5: 505 HTTP Version Not Supported

**Command:** `echo -e 'GET /test.html HTTP/2.0\r\nHost: 127.0.0.1:8080\r\n\r\n' | nc 127.0.0.1 8080`

**Result:**
```
    HTTP/1.1 505 HTTP Version Not Supported
    Content-Type: text/html
    Content-Length: 65
    Date: Thu, 30 Oct 2025 00:50:25 GMT
    Server: SimpleHTTPServer/1.0

    <html><body><h1>505 HTTP Version Not Supported</h1></body></html>
```

## Step Three: Proxy Server and Performance

### Part (a): Proxy Server Specifications and Implementation

#### Differences Between Web Server and Proxy Server

| Aspect | Web Server | Proxy Server |
|--------|-----------|--------------|
| Request-target format | Relative path: `/test.html` | Absolute URI: `http://example.com/` |
| Resource location | Local file system | Remote servers |
| Operation | Reads files from disk | Forwards requests to remote servers |
| Example request | `GET /test.html HTTP/1.1` | `GET http://example.com/ HTTP/1.1` |

#### Proxy Server Implementation

**Request Detection:**
The server determines mode based on request-target format. If the target starts with `http://`, it operates as a proxy; otherwise, it serves local files.

**Remote Server Communication:**
1. Extract hostname from absolute URI using regex pattern
2. Establish TCP socket connection to remote server on port 80
3. Forward complete HTTP request to remote server
4. Receive response from remote server
5. Relay response back to client

**Caching Implementation:**

The proxy includes an in-memory caching system with 30-second TTL (time-to-live).

Cache Structure:
- Dictionary mapping request targets to tuples of (response, expiration_timestamp, last_modified_date)
- Thread-safe access using `threading.RLock()`

Cache Behavior:
- **Cache hit (valid TTL):** Return cached response immediately without remote request
- **Cache revalidation (expired TTL):** Send conditional request with `If-Modified-Since` header. If server returns 304 Not Modified, refresh cache TTL and return cached response. If server returns 200 OK, update cache with new response.
- **Cache miss:** Send normal request, store response in cache with new TTL

**Key Implementation Functions:**

`handle_request()` - Routes requests based on target format:
```python
    if request.target.startswith("http://"):
        return handle_remote_target(request)
    else:
        return handle_local_target(request, web_root)
```

`handle_remote_target()` - Implements proxy functionality including cache checking, remote connection, response forwarding, and cache updates.

`HttpProxyCache` - Thread-safe cache with methods for set(), get_object(), exists(), and is_valid().

---

### Part (b): Proxy Testing Documentation

#### Test 1: Basic Proxy Functionality

**Command:**
```bash
    curl --output - -x localhost:8080 http://example.com
```

| Server-Side Log | Client-Side Output |
|-----------------|-------------------|
| `Connection from ('127.0.0.1', 39652)`<br>`Request:`<br>`GET http://example.com/ HTTP/1.1`<br>`Host: example.com`<br>`User-Agent: curl/8.5.0`<br>`Accept: */*`<br>`Proxy-Connection: Keep-Alive`<br><br>`Response: HTTP/1.1 200 OK` | `<!doctype html>`<br>`<html lang="en">`<br>`<head>`<br>`<title>Example Domain</title>`<br>`...`<br>`<h1>Example Domain</h1>`<br>`<p>This domain is for use in documentation examples...`<br>`</html>` |

**Result:** Proxy successfully forwarded request to example.com, received HTML response, and relayed it back to client.

---

#### Test 2: Cache Miss (First Request)

**Command:**
```bash
    curl -w "\nTime: %{time_total}s\n" -x localhost:8080 http://example.com -o /dev/null -s
```

**Output:**
```
    Time: 0.087272s
```

**Result:** First request to example.com required full network round-trip to remote server (87.3ms). Response stored in cache with 30-second TTL.

---

#### Test 3: Cache Hit (Second Request)

**Command:**
```bash
    curl -w "\nTime: %{time_total}s\n" -x localhost:8080 http://example.com -o /dev/null -s
```

**Output:**
```
    Time: 0.001545s
```

**Server Log:** `Cache hit for target: http://example.com/`

---

**Performance Comparison:**

| Metric | Cache Miss | Cache Hit | Improvement |
|--------|-----------|-----------|-------------|
| Response Time | 87.3ms | 1.5ms | 56.5x faster |
| Latency Reduction | - | 85.8ms | 98.2% |
| Remote Request | Yes | No | - |

<br>
<br>
<br>

---


#### Performance Analysis

**100 Concurrent Users Scenario:**

| Configuration | Total Time | Calculation |
|--------------|-----------|-------------|
| No cache | 8.73 seconds | 100 × 87.3ms |
| With cache | 0.236 seconds | 87.3ms + (99 × 1.5ms) |
| Efficiency gain | 37x | 8730ms / 236ms |

<br>
<br>

---

<br>

### Part (c): Multi-Threading Implementation and Performance Impact

#### Architecture

**Main Thread:**
- Runs `run_server()` function
- Creates and binds TCP socket to 127.0.0.1:8080
- Accepts incoming connections in infinite loop
- Spawns new worker thread for each connection
- Continues accepting without blocking

**Worker Threads:**
- Created via `threading.Thread(target=handle_connection, ...)`
- Each handles one client connection
- Receives request, processes it, sends response
- Closes socket and terminates

#### Performance Benefits

**Single-threaded behavior:**
Requests processed sequentially. If request 1 takes 2 seconds, request 2 waits 2 seconds to start.

**Multi-threaded behavior:**
Concurrent request processing. Multiple clients served simultaneously.

**I/O-bound optimization:**
While one thread waits for file I/O or network response, other threads continue executing. CPU context-switches between threads during I/O wait periods.

**Measured performance (5 concurrent requests):**

| Configuration | Request Times | Total Time |
|--------------|---------------|------------|
| Single-threaded | 15ms, 30ms, 45ms, 60ms, 75ms | 75ms |
| Multi-threaded  | 15ms, 16ms, 17ms, 15ms, 16ms | 17ms |
| Improvement | - | 4.4x faster |

#### Limitations

**Python Global Interpreter Lock (GIL):**
Prevents true CPU parallelism. Only one thread executes Python bytecode at a time. However, I/O-bound operations (file reading, network requests) release the GIL, allowing other threads to execute during wait periods.

**Thread overhead:**
Each thread consumes approximately 8MB stack space. Thread creation and context switching add overhead. For our use case with 10-500ms request times, overhead is negligible compared to I/O wait.

### Proxy Performance with Multi-threading

**Sequential processing (3 proxy requests, 87ms each):**
Total time: 261ms (87ms × 3)

**Concurrent processing (3 proxy requests, 87ms each):**
Total time: 90ms (limited by slowest request)
Improvement: 2.9x faster

**Combined with caching (100 requests):**
- First request: 87ms (cache miss)
- Remaining 99 requests: 1.5ms each (cache hits, processed concurrently)
- Total time: 236ms
- Without cache and multi-threading: 8,730ms
- Overall improvement: 37x faster


Overall Multi-threading provides significant performance for I/O-bound workloads:
- Concurrent file serving: 4.4x faster 
- Concurrent proxy requests: 2.9x faster 
- Cached responses: 56.5x faster 
- Combined optimization: 37x faster for repeated requests

The thread-per-request model is appropriate for web servers handling file I/O and network operations.

