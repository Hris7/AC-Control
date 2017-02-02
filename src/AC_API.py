#!/usr/bin/env python
# coding: utf-8

'''
Created on 29.01.2017

@author: Christopher Köck
'''

import AC_Settings
import web
from web import webapi
import pigpio
import json
from  AC_CommandBuilder import CommandBuilder
from AC_SendIR import SimpleSendIR
from AC_SendIR import Sender
import exceptions

VERSION = "v1"

urls = (
    '/AC_SendIR', 'acSendIr'
)


# 200 - ok
# 403 - version falsch
# 401 - auth falsch
# 422 - request falsch


# {
#   "version": "v1",
#   "auth": "asdf1234",
#   "power": "on",
#   "mode": "cool",
#   "temp": 20,
#   "fanSpeed": "auto",
#   "swing": "off",
#   "setAirflow": false,
#   "powerful": false,
#   "economy": false
# }

def HTTP401():
    return webapi.HTTPError("401 Unauthorized", {"WWW-Authenticate" : "If you don't know how to authenticate, don't call this API", "Content-Type" : "text/html"}, "401 Unauthorized")
def HTTP403():
    return webapi.HTTPError("403 Forbidden", {"Content-Type" : "text/html"}, "Please update your Client")
def HTTP422(message=None):
    return webapi.HTTPError("422 Unprocessable Entity", {"Content-Type" : "text/html"}, message or "422 Unprocessable Entity")
def HTTP500(message=None):
    return webapi.HTTPError("500 Internal Server Errory", {"Content-Type" : "text/html"}, message or "500 Internal Server Error")

class acSendIr():
    def POST(self):
        data = json.loads(web.data())
        for key in data:
            print key + " = " + str(data[key])
        # Check Version
        if data["version"] != VERSION:
            raise HTTP403()
        # Check auth
        if data["auth"] != AC_Settings.PASSWORD:
            raise HTTP401()
        # Check Commands
        checkResult = CommandBuilder.check(data)
        if checkResult != "ok":
            raise HTTP422(checkResult)
        
        # Connect to Pi.   
        print "Connect to Pi. (API)"
        pi = pigpio.pi()   
        if not pi.connected:
            return HTTP500("Can't connect to pigpio :(")
        cB = CommandBuilder(data)
        command = cB.build()
        print command
        Sender().send(pi, command)
        pi.stop()
                
        return "ok"

class Server():
    def startServer(self):
        app = web.application(urls, globals())
        app.run()  
    
if __name__ == "__main__":
    Server().startServer()
