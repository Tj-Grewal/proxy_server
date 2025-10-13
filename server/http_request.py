"""
Responsibility: parse the request line and headers, create a Request object with fields:
method, path, http_version, headers (dict), body (bytes or None).

Error cases: malformed request line -> return parse error (used to generate 400 or 505).
"""