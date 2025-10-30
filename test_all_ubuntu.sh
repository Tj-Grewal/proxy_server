#!/bin/bash
# HTTP Server Status Code Testing Guide for Ubuntu/Linux

# Test 1: 200 OK
echo "TEST 1: 200 OK - Valid GET request"
echo "Command: curl -i http://127.0.0.1:8080/test.html"
echo "----------------------------------------"
curl -i http://127.0.0.1:8080/test.html
echo ""
echo ""

# Test 2: 304 Not Modified
echo "TEST 2: 304 Not Modified - Conditional request"
echo "Command: curl -i -H 'If-Modified-Since: Sat, 01 Jan 2030 00:00:00 GMT' http://127.0.0.1:8080/test.html"
echo "----------------------------------------"
curl -i -H "If-Modified-Since: Sat, 01 Jan 2030 00:00:00 GMT" http://127.0.0.1:8080/test.html
echo ""
echo ""

# Test 3: 403 Forbidden
echo "TEST 3: 403 Forbidden - Path traversal attack"
echo "Command: curl --path-as-is -i http://127.0.0.1:8080/../test.html"
echo "----------------------------------------"
curl --path-as-is -i http://127.0.0.1:8080/../test.html
echo ""
echo ""

# Test 4: 404 Not Found
echo "TEST 4: 404 Not Found - Non-existent file"
echo "Command: curl -i http://127.0.0.1:8080/nonexistent.html"
echo "----------------------------------------"
curl -i http://127.0.0.1:8080/nonexistent.html
echo ""
echo ""

# Test 5: 505 HTTP Version Not Supported
echo "TEST 5: 505 HTTP Version Not Supported - HTTP/2.0 request"
echo "Command: echo -e 'GET /test.html HTTP/2.0\\r\\nHost: 127.0.0.1:8080\\r\\n\\r\\n' | nc 127.0.0.1 8080"
echo "----------------------------------------"
echo -e "GET /test.html HTTP/2.0\r\nHost: 127.0.0.1:8080\r\n\r\n" | nc 127.0.0.1 8080
echo ""
echo ""

# Test 6: HTTP Proxy without caching
echo "TEST 6: HTTP Proxy without caching"
echo "Command: curl --output - -x localhost:8080 example.com"
echo "----------------------------------------"
curl --output - -x localhost:8080 example.com
echo ""
echo ""
