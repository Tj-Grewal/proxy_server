## Web & Web Proxy Servers

### Step One: Determine Requirements (10 points)

At this step, you need to find out the details needed to implement your web server. We need you to implement a simple web server that is able to process and respond to HTTP requests. Your web server should be able to respond to requests with the following messages for the relevant methods to the client. Therefore, for each item you need to decide what are the requirements in the request, what method is used, and what part of the message is causing the specified status code in the response (2 points for each item):

Code:	Message
200: 	OK
304:	Not Modified
403:	Forbidden
404:	Not Found
505:	HTTP Version Not Supported

Please feel free to consult RFC 7231Links to an external site., Section 6 for details of the Status Codes.

The deliverable of this step is writing down the specifications of the logic for the generation of each of these status codes (1 point each), and the HTTP request message you will use to test it (1 point each).

### Step Two: Build Your Minimal Web Server & Test (10 points)

(a) You can start this step once you have seen socket programming at the end of Module (2). In this part of your MP, using what you learned about socket programming and HTTP protocol, we require you to create your simple web server. Note that you are not allowed to use the Python HTTP module for this project.

Note that HTTP protocol is a request/response protocol. Therefore, implementing a Web Server means writing code for a server that can receive HTTP messages sent to a known port number that is listening to client requests, processing those requests, and responding to them.

(b) To test your web server for the correct working scenario, copy test.html Download test.htmlin the main directory of your web server. Then find out the IP address of your machine (or use the local host address), and the port used in the code for the web server and type the following in your web browser (2 points):

http://IP_ADDRESS:PORT/test.html

(c) Now you need to test your web server for generating the status codes provided in step one. You can use curl, telnet, or your browser for each of these steps. You can also edit your test file, or send the request properly to test your implementation for different message scenarios. Print screen, or cut and paste the output and document your test procedures. (8 points)

### Step Three: Performance (18 points)

(a) Think about a web proxy server. What is different in request handling in a proxy server and a web server that hosts your files? Write down the detailed specifications you come up with for a minimal proxy server only using the knowledge you have from module (2) slides 29-34 (and consulting RFCs), and implement them (10 points).

(b) Decide the test procedure to show the working of your proxy server. You need to describe and find ways to test your server-side functionality.
Print screen, or cut and past output and document your test procedures to show. (5 points)

(c) Is your Web Server a single-thread server or a multi-thread one? If it is a single-thread server, expand it to respond to parallel requests in different threads. Explain in the report document why your web server is a multi-thread server and how that impacts performance. (3 points)

(Optional) Step Four: Expand (5 Bonus Points)

Make changes to your server to avoid the HOL problem using frames (3 points), and explain what you have done (2 points).
Note: Please check Module (2) Slide 38 for more details.

 

Deliverables
For steps one to four, please make a zip file including:

Your web server code (.py)
Your (if any) modified test files (.html)
A  report (.pdf) file including specifications of status code generation logic, proxy requirements, and your test procedures including the request message details for all steps, and print screens
Submit the zip to this activity in Canvas. One submission will be enough for each group (should automatically show for both group members).


Resources
[1] RFC 7231 (https://tools.ietf.org/html/rfc7231.htmlLinks to an external site.), Section 6
[2] RFC 7540 (https://tools.ietf.org/html/rfc7540Links to an external site.)
[3] https://docs.python.org/3/howto/sockets.htmlLinks to an external site.
Also covered in IS(3): UDP, IS(4): TCP, and IS(6): RAW
[4] https://docs.python.org/3/library/threading.htmlLinks to an external site.
[5] Web Proxy (Not a Standard - architecture in section 3.2.2 is intended): https://www.ietf.org/rfc/rfc3040.txtLinks to an external site.

Note (1): You are not allowed to use the Python HTTP modules/libraries. You are allowed to consult IETF RFCs for everything.

Note (2): The steps could be additively implemented on the same server Python file. However, if you are not sure and afraid that your changes will impact your previous step's output, you can mention that in your report and include multiple Python files, one for each step.
