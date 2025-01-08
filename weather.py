#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import requests
import re
import datetime
from datetime import date,timedelta

from bs4 import BeautifulSoup

# 25/01/08 v1.07 現在の気温を取得するメソッド追加
version = "1.07"  

out =  ""
logf = ""
appdir = os.path.dirname(os.path.abspath(__file__))
#  出力ファイル名の形式    we.yymmdd_hh.txt   (データ開始の日時)
outfile_prefix = appdir + "/data/we" 
week_outfile_prefix = appdir + "/week/we" 
conffile = appdir + "/weather.conf"
res = ""
week_data_interval = 6   #  週間天気で何時間起きにデータを採取するか
icon_url = "https://gvs.weathernews.jp/onebox/img/wxicon/"     # 天気アイコンのURL
icon_url_week = "//gvs.weathernews.jp/onebox/img/wxicon/"

def main_proc() :
    read_config()
    date_settings()
    access_site()
    analize()
    temperature = get_current_temperature()
    analize_week()
    output_datafile()
    output_week_datafile()

def access_site() :
    global res

    if not proxy == "noproxy" :
        os.environ['https_proxy'] = proxy

    res = requests.get(target_url,verify=False)
    res.encoding = res.apparent_encoding

def output_datafile() :
    
    #today_hh = today_datetime.hour     #  現在の 時

    # 開始日 start_dd には月の情報がないため今日の日付から 開始日付 を作成する
    start_mm = today_mm
    start_yy = today_yy
    if start_dd > today_dd :    # 月をまたいでいる
        start_mm = today_mm - 1 
        if start_mm == 0 :
            start_mm = 12
            start_yy = today_yy - 1 
    start_date = datetime.date(start_yy, start_mm , start_dd)

    cur_date = start_date
    dd = cur_date.day
    hh = start_hh
    data_list = []
    rec_hh = ""      # ファイルに記録する最初の 時
    #  ファイルには現在の 日付 時  以降のものだけ出力する
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

def output_week_datafile() :
   
    if (today_hh % 3) != 0 :    # 3時間おきに採取
        return 

    # 開始日 start_dd には月の情報がないため今日の日付から 開始日付 を作成する
    start_mm = today_mm
    start_yy = today_yy
    if week_start_dd > today_dd :    # 月をまたいでいる
        start_mm = today_mm - 1 
        if start_mm == 0 :
            start_mm = 12
            start_yy = today_yy - 1 
    start_date = datetime.date(start_yy, start_mm , week_start_dd)

    cur_date = start_date
    data_list = []
    #  ファイルには現在の 日付 以降のものだけ出力する
    for we in week_list :
        if cur_date < today_date :
            cur_date +=  datetime.timedelta(days=1)
            continue
        data_list.append(we)
        cur_date +=  datetime.timedelta(days=1)

    outfile = week_outfile_prefix + f'{today_yy-2000}{today_mm:02}{today_dd:02}_{today_hh:02}.txt' 
    out = open(outfile , 'w', encoding='utf-8')
    s = str(today_date) + " " + str(today_hh) + "\n"
    out.write(s)
    s = ",".join(map(str, data_list))
    out.write(s)
    out.write("\n")
    out.close()

#   1時間天気の情報を取得
#      start_dd   記録されている最初の  日   (月の情報はない)
#      start_hh   記録されている最初の  時
#      we_list    1時間毎の天気  list 
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
        icon = icon.replace(icon_url,"")
        icon = int(icon.replace(".png",""))
        we_list.append(icon)

#   現在時刻の気温を取得する
def get_current_temperature() :
    top = BeautifulSoup(res.text, 'html.parser')
    div_1hour = top.find('div', id ='flick_list_1hour')
    daily_items = div_1hour.find_all('div', class_ ='group')
    for daily in daily_items :              # 日 ごとのループ
        div_date = daily.find('div', class_ ='date')
        dd = div_date.text.strip()
        dd = int(re.sub(r"\D", "", dd))     # 数字部分を抜き出す
        if dd != today_dd :
            continue 
        #print(f'dd = {dd}')
        hour_items = daily.find_all('ul', class_ ='list')
        for hour in hour_items :            # 時 ごとのループ
            time_data = hour.find('li', class_ ='time')  
            hh = int(time_data.text)
            #print(f'hh= {hh}')
            if hh != today_hh :
                continue 
            te = hour.find('li', class_ ='temp')    # 気温
            temperature = te.text.strip()
            temperature = int(re.sub(r"\D", "", temperature))     # 数字部分を抜き出す
            #print(temperature)
            break
    return temperature

def analize_week() :
    global week_start_dd , week_list 
    top = BeautifulSoup(res.text, 'html.parser')
    div_week = top.find('div', id ='flick_list_week')
    weather_items = div_week.find_all('ul', class_ ='wxweek_content')
    week_start_dd = 0
    week_list = []
    for w in weather_items :
        div_date = w.find('li', class_ ='date') 
        div_day = div_date.find('p', class_ ='day') 
        dd = int(div_day.text)
        if week_start_dd == 0 :    #  最初の日付
            week_start_dd = dd
        img = w.find('img', class_ = 'wx__icon' )
        icon = img.get('src')
        icon = icon.replace(icon_url_week,"")
        icon = int(icon.replace(".png",""))
        week_list.append(icon)

def date_settings():
    global  today_date,today_mm,today_dd,today_yy,today_datetime,today_hh

    today_datetime = datetime.datetime.today()   # datetime 型
    today_date = datetime.date.today()           # date 型
    today_mm = today_date.month
    today_dd = today_date.day
    today_yy = today_date.year
    today_hh = today_datetime.hour     #  現在の 時

def read_config() : 
    global target_url,proxy,debug,ftp_host,ftp_user,ftp_pass,ftp_url
    if not os.path.isfile(conffile) :
        debug = 1 
        return

    conf = open(conffile,'r', encoding='utf-8')
    target_url = conf.readline().strip()
    proxy  = conf.readline().strip()
    ftp_host = conf.readline().strip()
    ftp_user = conf.readline().strip()
    ftp_pass = conf.readline().strip()
    ftp_url = conf.readline().strip()
    debug = int(conf.readline().strip())
    conf.close()

# -------------------------------------------------------------
main_proc()
