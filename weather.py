#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import requests
import urllib.parse
import codecs

from bs4 import BeautifulSoup
from datetime import datetime

version = "0.01"     # 24/10/04 v0.01  
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
    div_date = div_1hour.find('div', class_ ='date')    # 最初に出てくる  日
    print(div_date.text)
    
    time_data = div_1hour.find('li', class_ ='time')    # 最初に出てくる  時
    print(time_data.text)

    weather_items = div_1hour.find_all('li', class_ ='weather')
    for w in weather_items :
        img = w.find('img' ,class_ = "wx__icon")
        icon = img.get('src')
        print(icon)

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
