INPUT: 

python http_server.py
Server listening on http://127.0.0.1:8080

Connection from ('127.0.0.1', 39586)
Request:
GET /test.html HTTP/1.1
Host: 127.0.0.1:8080
User-Agent: curl/8.5.0
Accept: */*

...
Response: HTTP/1.1 200 OK

Connection from ('127.0.0.1', 39602)
Request:
GET /test.html HTTP/1.1
Host: 127.0.0.1:8080
User-Agent: curl/8.5.0
Accept: */*
If-Modified-Since: Sat, 01 Jan 2030 00:00:00 GMT

...
Response: HTTP/1.1 304 Not Modified

Connection from ('127.0.0.1', 39608)
Request:
GET /../test.html HTTP/1.1
Host: 127.0.0.1:8080
User-Agent: curl/8.5.0
Accept: */*

...
Response: HTTP/1.1 403 Forbidden

Connection from ('127.0.0.1', 39624)
Request:
GET /nonexistent.html HTTP/1.1
Host: 127.0.0.1:8080
User-Agent: curl/8.5.0
Accept: */*

...
Response: HTTP/1.1 404 Not Found

Connection from ('127.0.0.1', 39636)
Request:
GET /test.html HTTP/2.0
Host: 127.0.0.1:8080


...
Error parsing request: Unsupported HTTP version

Connection from ('127.0.0.1', 39652)
Request:
GET http://example.com/ HTTP/1.1
Host: example.com
User-Agent: curl/8.5.0
Accept: */*
Proxy-Connection: Keep-Alive

...
Response: HTTP/1.1 200 OK


OUTPUT:

./test_all_ubuntu.sh
TEST 1: 200 OK - Valid GET request
Command: curl -i http://127.0.0.1:8080/test.html
----------------------------------------
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


TEST 2: 304 Not Modified - Conditional request
Command: curl -i -H 'If-Modified-Since: Sat, 01 Jan 2030 00:00:00 GMT' http://127.0.0.1:8080/test.html
----------------------------------------
HTTP/1.1 304 Not Modified
Content-Type: text/html
Content-Length: 0
Date: Thu, 30 Oct 2025 00:50:24 GMT
Server: SimpleHTTPServer/1.0
Last-Modified: Sun, 26 Oct 2025 03:52:50 GMT



TEST 3: 403 Forbidden - Path traversal attack
Command: curl --path-as-is -i http://127.0.0.1:8080/../test.html
----------------------------------------
HTTP/1.1 403 Forbidden
Content-Type: text/html
Content-Length: 69
Date: Thu, 30 Oct 2025 00:50:24 GMT
Server: SimpleHTTPServer/1.0

<html><body><h1>403 Forbidden</h1><p>Access denied.</p></body></html>     

TEST 4: 404 Not Found - Non-existent file
Command: curl -i http://127.0.0.1:8080/nonexistent.html
----------------------------------------
HTTP/1.1 404 Not Found
Content-Type: text/html
Content-Length: 92
Date: Thu, 30 Oct 2025 00:50:25 GMT
Server: SimpleHTTPServer/1.0

<html><body><h1>404 Not Found</h1><p>The requested resource was not found.</p></body></html>

TEST 5: 505 HTTP Version Not Supported - HTTP/2.0 request
Command: echo -e 'GET /test.html HTTP/2.0\r\nHost: 127.0.0.1:8080\r\n\r\n' | nc 127.0.0.1 8080
----------------------------------------
HTTP/1.1 505 HTTP Version Not Supported
Content-Type: text/html
Content-Length: 65
Date: Thu, 30 Oct 2025 00:50:25 GMT
Server: SimpleHTTPServer/1.0

<html><body><h1>505 HTTP Version Not Supported</h1></body></html>

TEST 6: HTTP Proxy without caching
Command: curl --output - -x localhost:8080 example.com
----------------------------------------
<!doctype html><html lang="en"><head><title>Example Domain</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}h1{font-size:1.5em}div{opacity:0.8}a:link,a:visited{color:#348}</style><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.<p><a href="https://iana.org/domains/example">Learn more</a></div></body></html>