#!/usr/bin/env python
# coding: utf-8

'''
Created on 29.01.2017

@author: Christopher Köck
'''
from AC_SendIR import SimpleSendIR
from AC_API import Server



if __name__ == '__main__':
    SimpleSendIR()
    Server().startServer()
