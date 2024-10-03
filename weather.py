#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import requests
import urllib.parse
import codecs

from bs4 import BeautifulSoup
from datetime import datetime

version = "0.00"     # 24/10/03 v0.00  開発開始
out =  ""
logf = ""
appdir = os.path.dirname(os.path.abspath(__file__))
conffile = appdir + "/weather.conf"
res = ""

def main_proc() :
    read_config()
    access_site()
    analize()

def access_site() :
    global res

    if not proxy == "noproxy" :
        os.environ['https_proxy'] = proxy

    res = requests.get(target_url,verify=False)
    res.encoding = res.apparent_encoding

def analize() :
    top = BeautifulSoup(res.text, 'html.parser')
    div_1hour = top.find('div', id ='flick_list_1hour')
    #div_1hour = top.find_all(id ='flick_list_1hour')
    div_date = div_1hour.find('div', class_ ='date')
    print(div_date.text)

def read_config() : 
    global target_url,proxy,debug
    if not os.path.isfile(conffile) :
        debug = 1 
        return

    conf = open(conffile,'r', encoding='utf-8')
    target_url = conf.readline().strip()
    proxy  = conf.readline().strip()
    debug = int(conf.readline().strip())
    conf.close()

# -------------------------------------------------------------
main_proc()
