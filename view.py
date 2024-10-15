#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import datetime
from datetime import date,timedelta
#from datetime import datetime

# 24/10/15 v0.02 複数ファイルに対応中
version = "0.02"     

out =  ""
logf = ""
appdir = os.path.dirname(os.path.abspath(__file__))
datafile = appdir + "/data/we.txt" 
datadir = appdir + "/data/" 
outfile = appdir + "/weather.htm" 
conffile = appdir + "/weather.conf"
res = ""

#    データ形式
#    辞書   {発表日時 :  {予報日時 : 予報天気 , 予報日時 : 予報天気 , ....}}
#      発表日時 はその予報が発表された日時    mmddhh をintとして持つ    発表日時はデータ最初の日時から 2日4時間後？
#      予報日時 予報天気の日時  mmddhh をintとして持つ
#      予報天気 int
#    例  
#    発表日時      予報日時     予報天気   予報日時     予報天気
#    10/01 01:00  10/01 12:00  100       10/01 13:00     200   ... この1行が 1ファイル
#    10/01 02:00  10/01 12:00  100       10/01 13:00     100 
#    10/01 03:00  10/01 12:00  100       10/01 13:00     300
#    以下のデータになる
#    100112  {100101:100 , 100102 : 100, 100103 : 200, ....}
#    100113  {100101:200 , 100102 : 100, 100103 : 300, ....}
we_data = {}


def main_proc() :
    #read_config()
    #output_datafile()
    #output_result()

    dir_path = datadir

    datafile_list = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]
    #print(datafile_list)
    read_data(datafile_list[0])

    #for fname in datafile_list :
    #    read_data(fname)
    output_html()

def read_data(fname) : 
    global start_date,start_hh,we_list
    datafile = datadir + fname
    f = open(datafile , 'r')
    header  = f.readline().strip()
    hh = header.split()
    date_str = hh[0]
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    start_date = datetime.date(dt.year, dt.month, dt.day)
    start_date_int = conv_date_int(start_date)

    start_hh = int(hh[1])
    cur_hh = start_hh
    body  = f.readline().strip()
    we_list = body.split(",")
    #print(we_list)
    f.close()
    for we in we_list :
        k = start_date_int + cur_hh


def conv_date_int(d) :
    i = d.month * 10000 + d.day * 100 
    return i

def output_html() :
    
    out = open(outfile , 'w', encoding='utf-8')

    out.write("<table><tr><th>日付</th><th>時間</th><th>天気</th></tr>\n")
    cur_date = start_date
    cur_hh = start_hh
    for we in  we_list :
        out.write(f'<tr><td>{cur_date}</td><td>{cur_hh}</td><td>'
        f'<img src="https://weathernews.jp/onebox/img/wxicon/{we}.png" width="40" height="30"></td></tr>\n')
        cur_hh += 1
        if cur_hh == 24 :
            cur_hh = 0
            cur_date +=  datetime.timedelta(days=1)

    out.write("</table>\n")
    out.close()

def output_datafile() :
    today_date = date.today()
    cur_mm =  today_date.month    #  今月
    cur_yy =  today_date.year    #  今月
    start_date = datetime.date(cur_yy, cur_mm , start_dd)
    out = open(outfile , 'w', encoding='utf-8')
    s = str(start_date) + " " + str(start_hh) + "\n"
    out.write(s)
    s = ",".join(map(str, we_list))
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
