#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import requests
import urllib.parse
import codecs
import re
import datetime
from datetime import date,timedelta
#from datetime import datetime

from bs4 import BeautifulSoup

# 24/10/15 v0.05 過去のデータは出力しないようにした
version = "0.05"     

out =  ""
logf = ""
appdir = os.path.dirname(os.path.abspath(__file__))
#  出力ファイル名の形式    we.yymmdd_hh.txt   (データ開始の日時)
outfile_prefix = appdir + "/data/we" 
conffile = appdir + "/weather.conf"
res = ""

def main_proc() :
    read_config()
    access_site()
    analize()
    output_datafile()
    #output_result()

def access_site() :
    global res

    if not proxy == "noproxy" :
        os.environ['https_proxy'] = proxy

    res = requests.get(target_url,verify=False)
    res.encoding = res.apparent_encoding

def output_datafile() :
    today_date = date.today()
    today_mm =  today_date.month    #  今月
    today_yy =  today_date.year    #  今年
    today_dd =  today_date.day    #  今年
    today_datetime = datetime.datetime.today()
    today_hh = today_datetime.hour

    #  TODO:  月を考慮する必要あり
    start_date = datetime.date(today_yy, today_mm , start_dd)

    cur_date = start_date
    dd = cur_date.day
    hh = start_hh
    data_list = []
    rec_hh = ""      # ファイルに記録する最初の 時
    for we in we_list :
        if hh == 24 :
            hh = 0
            cur_date +=  datetime.timedelta(days=1)
        if cur_date < today_date :
            hh += 1
            continue
        if hh <  today_hh :
            hh += 1
            continue
        if rec_hh == "" :
            rec_hh = hh
        data_list.append(we)


    outfile = outfile_prefix + f'{today_yy-2000}{today_mm:02}{today_dd:02}_{rec_hh:02}.txt' 
    out = open(outfile , 'w', encoding='utf-8')
    s = str(today_date) + " " + str(rec_hh) + "\n"
    out.write(s)
    s = ",".join(map(str, data_list))
    out.write(s)
    out.write("\n")
    out.close()

def output_result() :
    today_date = date.today()
    cur_mm =  today_date.month    #  今月
    cur_yy =  today_date.year    #  今月
    start_date = datetime.date(cur_yy, cur_mm , start_dd)
    cur_date = start_date
    cur_hh = start_hh
    print(start_date)
    for we in  we_list :
        print(cur_date,cur_hh,we)
        cur_hh += 1
        if cur_hh == 24 :
            cur_hh = 0
            cur_date +=  datetime.timedelta(days=1)

def analize() :
    global start_dd,start_hh,we_list

    top = BeautifulSoup(res.text, 'html.parser')
    div_1hour = top.find('div', id ='flick_list_1hour')
    div_date = div_1hour.find('div', class_ ='date')    # 最初に出てくる  日
    start_dd = div_date.text.strip()
    start_dd = int(re.sub(r"\D", "", start_dd))     # 数字部分を抜き出す
    
    time_data = div_1hour.find('li', class_ ='time')    # 最初に出てくる  時
    start_hh = int(time_data.text)

    weather_items = div_1hour.find_all('li', class_ ='weather')
    we_list = []
    for w in weather_items :
        img = w.find('img' ,class_ = "wx__icon")
        icon = img.get('src')
        icon = icon.replace("https://weathernews.jp/onebox/img/wxicon/","")
        icon = int(icon.replace(".png",""))
        we_list.append(icon)

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
