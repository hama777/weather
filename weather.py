#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import requests
import re
import datetime
from datetime import date,timedelta

from bs4 import BeautifulSoup

# 25/08/07 v1.14 降水量を取得ができなかったのを修正
version = "1.14"  

out =  ""
logf = ""
appdir = os.path.dirname(os.path.abspath(__file__))
#  出力ファイル名の形式    we.yymmdd_hh.txt   (データ開始の日時)
outfile_prefix = appdir + "/data/we" 
week_outfile_prefix = appdir + "/week/we" 
conffile = appdir + "/weather.conf"
temperafile = appdir + "/temperature.txt"    #  実績気温データ  
precipitationfile = appdir + "/precipitation.txt"    #  実績降水量データ  
act_weather_file = appdir + "/actweather.txt"   #  実績天気データ  1時間ごと  暫定
res = ""
week_data_interval = 6   #  週間天気で何時間起きにデータを採取するか
icon_url = "https://gvs.weathernews.jp/onebox/img/wxicon/"     # 天気アイコンのURL
icon_url_week = "//gvs.weathernews.jp/onebox/img/wxicon/"

def main_proc() :
    global temperature
    read_config()
    date_settings()
    access_site()
    analize()
    temperature = get_current_temperature()
    analize_week()
    output_datafile()
    output_week_datafile()
    output_temperature()
    output_precipitation()

def access_site() :
    global res

    if not proxy == "noproxy" :
        os.environ['https_proxy'] = proxy

    res = requests.get(target_url,verify=False)
    res.encoding = res.apparent_encoding

def output_datafile() :
    
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
    datefmt = f'{today_yy-2000}{today_mm:02}{today_dd:02}{rec_hh:02}' 
    # データの先頭 data_list[0] が実際の天気を示す
    output_act_weather(datefmt,data_list[0])

#   実際の天気をファイルに出力する
#   act_weather_file に yymmddhh tab 天気コード の形式で追記する
def output_act_weather(fmt,act) :
    actf = open(act_weather_file , 'a', encoding='utf-8')
    actf.write(f'{fmt}\t{act}\n')
    actf.close()


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

#   気温データの出力
#      形式  yy/mm/dd hh:00 tab 気温
def output_temperature() :
    dt = f'{today_yy-2000}/{today_mm:02}/{today_dd:02} {today_hh:02}:00'
    out = open(temperafile , 'a', encoding='utf-8')
    out.write(f'{dt}\t{temperature}\n')
    out.close()

def output_precipitation() :
    precipitation = get_current_precipitation()
    dt = f'{today_yy-2000}/{today_mm:02}/{today_dd:02} {today_hh:02}:00'
    out = open(precipitationfile , 'a', encoding='utf-8')
    out.write(f'{dt}\t{precipitation}\n')
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

#   現在時刻の気温を取得する  New
def get_current_temperature() :
    top = BeautifulSoup(res.text, 'html.parser')
    obs_block = top.find('li', class_ ='obs_block')    # 気温は1つめにあるので find で取得
    val = obs_block.find('p', class_ ='value')    
    return  val.text

#   降水量を取得する
#       実況天気・観測値 から取得   先頭業は必ずしもその時刻でない可能性があるがとりあえず最新時のものを取得
def get_current_precipitation() :
    top = BeautifulSoup(res.text, 'html.parser')
    dataTable = top.find('table', class_ ='dataTable')   
    row = dataTable.find_all('tr') 
    col = row[1].find_all('td')     # 最新時は2行目 row[1] にある
    return float(col[4].text)         # 降水量は5カラム目 col[4] にある

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
