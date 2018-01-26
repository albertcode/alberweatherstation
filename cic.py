#!/usr/bin/env python
# encoding=utf8
'''
    File name: cic.py
    Description: Check the network connection and if it is down, reboot the system
    Python Version: 2.7.13
'''
__author__ = "Alberto Andrés"
__license__ = "GPL"

from urllib import urlopen
from os import system

try:
    urlopen("http://www.google.com")
    status = "connected"
except:
    status = "not connected"

if status == "not connected":
    system('reboot')
