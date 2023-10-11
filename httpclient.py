#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

DEBUG = True

GET = 0
POST = 1
LOCALHOST = "127.0.0.1"

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body
    
    def __repr__(self):
        return f'Code: {self.code}\nBody:\n{self.body}'

class HTTPClient(object):

    def assign_host_port(self, url):
        url_obj = urllib.parse.urlparse(url)

        if DEBUG:
            print(url_obj)

        self.path = url_obj.path if url_obj.path else "/"

        regex = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}\b"
        if re.match(regex, url_obj.netloc):
            self.host, self.port = url_obj.netloc.split(":")
            self.port = int(self.port)

            if DEBUG:
                print(self.host, self.port)

            return

        #self.port = 443 if url_obj.scheme == "https" else 80
        self.port = 80
        #self.host = url_obj.netloc if url_obj.netloc[:4] == "www." else "www." + url_obj.netloc
        self.host = url_obj.netloc
        print(self.host, self.port)

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def get_code(self, data):
        sections = data.split("\r\n")
        fields = sections[0].split(" ")
        return fields[1]

    def get_headers(self, data):
        fields = data.split("\r\n")[1:] #ignore the GET / HTTP/1.1
        output = {}
        for field in fields:
            try:
                key,value = field.split(':', 1)
                output[key] = value
            except:
                continue

        return output

    def get_body(self, data):
        sections = data.split("\r\n\r\n")
        if len(sections) > 1:
            return sections[1]
            
        return ""
    
    def form_request(self, method, args):
        method_name = ['GET','POST'][method]
        nl = "\r\n"

        req = f'{method_name} {self.path} HTTP/1.1{nl}Host: {self.host}'
        
        if args and len(args) > 0:
            encoded = urllib.parse.urlencode(args)
            req += f'{nl}Content-Type: application/x-www-form-urlencoded{nl}Content-Length: {len(encoded)}{nl * 2}{encoded}'
        
        if DEBUG:
            print(req)

        return req + (nl * 2)
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        
        try:
            data = buffer.decode('utf-8')
        except:
            data = buffer.decode('iso-8859-1')

        return data

    def handle_transaction(self, method, url, args=None):
        self.assign_host_port(url)
        self.connect(self.host, self.port)

        # deal with sending request
        request = self.form_request(method, args)
        self.sendall(request)
        self.socket.shutdown(socket.SHUT_WR)

        # deal with receiving response
        data = self.recvall(self.socket)
        self.close()

        if DEBUG:
            print(data)

        code = self.get_code(data)
        body = self.get_body(data)
        return HTTPResponse(int(code), body)

    def GET(self, url, args=None):
        return self.handle_transaction(GET, url, args)

    def POST(self, url, args=None):
        return self.handle_transaction(POST, url, args)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
