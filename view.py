#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import locale
import datetime
from datetime import date,timedelta
#from datetime import datetime

# 24/11/08 v0.16 24時間的中率表示
version = "0.16"     

out =  ""
logf = ""
appdir = os.path.dirname(os.path.abspath(__file__))
datafile = appdir + "/data/we.txt" 
datadir = appdir + "/data/" 
resultfile = appdir + "/weather.htm" 
conffile = appdir + "/weather.conf"
templatefile = appdir + "/weather_templ.htm"
res = ""

#    we_data  データ形式
#    we_data = {
#        予報日時 : {発表日時 : 天気, 発表日時 : 天気, ... },
#        予報日時 : {発表日時 : 天気, 発表日時 : 天気, ... }
#    }
#      予報日時 予報天気の日時  mmddhh をintとして持つ
#      発表日時 はその予報が発表された日時  mmddhh をintとして持つ  ファイルの先頭に記録されている  
#      予報天気 int   100 晴れ  200  曇り  300 以上  雨
#    例  
#    発表日時      予報日時     予報天気   予報日時     予報天気
#    10/01 01:00  10/01 12:00  100       10/01 13:00     200   ... この1行が 1ファイル
#    10/01 02:00  10/01 12:00  100       10/01 13:00     100 
#    10/01 03:00  10/01 12:00  100       10/01 13:00     300
#    以下のデータになる
#    100112  {100101:100 , 100102 : 100, 100103 : 200, ....}
#    100113  {100101:200 , 100102 : 100, 100103 : 300, ....}
we_data = {}

#  天気コード
#  天気アイコンのURL は  https://weathernews.jp/onebox/img/wxicon/{天気コード}.png
#     100 500 550 600  晴れ  200  曇り  300  雨  650 小雨  400 450 雪   250  曇り 雪  800 曇り雷 850 大雨
icon_url = "https://weathernews.jp/onebox/img/wxicon/"

#   hit_rate 的中率のデータ
#   hit_rate 辞書  { yymmddhh : hitdata }
#      hitdata 辞書 { act : 実際の天気(int) , cnt : 総件数 , hit : ヒット件数}
hit_rate = {}

def main_proc() :
    locale.setlocale(locale.LC_TIME, '')
    date_settings()
    #read_config()

    dir_path = datadir

    datafile_list = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]
    for fname in datafile_list :
        read_data(fname)

    parse_template()

def read_data(fname) : 
    global start_date,start_hh,we_list

    datafile = datadir + fname
    f = open(datafile , 'r')
    header  = f.readline().strip()
    hh = header.split()
    date_str = hh[0]
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    start_date = datetime.date(dt.year, dt.month, dt.day) # データの開始日付 date型
    start_date_int = conv_date_int(start_date)            # データの開始日付 yymmddhh の int型 キーとして使用
    start_hh = int(hh[1])            # データの開始時刻

    body  = f.readline().strip()
    we_list = body.split(",")        #  we_list は1時間ごとの天気
    f.close()

    pub_date = start_date_int + start_hh   #  発表日時 int  yymmddhh  we_data のvalの辞書のキー として使用
    cur_hh = start_hh                # 以下のループで現在の時刻として使用  int 型
    cur_date = start_date            # 以下のループで現在の日付として使用  date 型

    for we in we_list :
        k = conv_date_int(cur_date) + cur_hh    #  we_data の key
        
        if k in we_data :       # すでにキーがある場合はそのキーに対応する辞書に追加する
            val = we_data[k]    # そのキーに対応する辞書
            val[pub_date] = we  # そのキーに対応する辞書 に天気を追加
            we_data[k] = val    # we_data にどの辞書を再格納
        else :
            timeline_dic = {}   # キーがない場合は辞書を作成し、we_data の値として格納する
            timeline_dic[pub_date] = we
            we_data[k] = timeline_dic
        cur_hh += 1
        if cur_hh == 24 :
            cur_hh = 0
            cur_date +=  datetime.timedelta(days=1)

def output_html() :

    out.write('<thead><tr><th>予報日時</th>\n')
    cur_date = today_date - datetime.timedelta(days=3)    # 予報は今日の3日前から
    cur_hh = start_hh        
    #  テーブルヘッダ出力
    while True :
        out.write(f'<th>{cur_date.day}<br>{cur_hh:02}</th>')
        cur_hh += 1
        if cur_hh == 24 :
            cur_hh = 0
            cur_date +=  datetime.timedelta(days=1)
        if cur_date > start_date  : # 
            break
    out.write("</tr>\n</thead>\n")

    out.write("<tbody>\n")
    for forecast_date in  we_data.keys() :     # 予報日時
        mmdd = int(forecast_date / 100)
        if mmdd < today_mm * 100 + today_dd :  # 昨日以前の情報は出さない
            continue 

        #print(f'{forecast_date} の天気')
        forecast_str = conv_mmddhh_to_str(forecast_date)
        out.write(f'<tr><td>{forecast_str}</td>\n')
        timeline_dic = we_data[forecast_date]
        cur_date = today_date - datetime.timedelta(days=3)    # 予報は今日の3日前から
        cur_hh = start_hh
        while True :
            k = conv_date_int(cur_date) + cur_hh    # k 発表日時
            if k in  timeline_dic :
                we = timeline_dic[k]
                out.write(f'<td><img src="{icon_url}{we}.png" width="20" height="15"></td>\n')
                #print(f'発表日時 {k} 天気 {we}')
            else :
                out.write("<td>--</td>")
            cur_hh += 1
            if cur_hh == 24 :
                cur_hh = 0
                cur_date +=  datetime.timedelta(days=1)
            if cur_date > start_date  : # 
                break
        out.write("</tr>\n")
        #print("---")
    out.write("</tbody>\n")

#   int の mmddhh 形式を入力し  dd(曜日)/hh  形式の文字列を返す
def conv_mmddhh_to_str(mmddhh) :
    mm = int(mmddhh / 10000)
    dd = int(mmddhh / 100 % 100)  
    hh = int(mmddhh % 100)
    dt = datetime.date(today_yy, mm, dd)
    s = dt.strftime("%d(%a)")
    s = f'{s}/{hh:02}'
    return s 

#   int の mmddhh 形式を入力し  date 型の値を返す
def conv_mmddhh_to_date(mmddhh) :
    mm = int(mmddhh / 10000)
    dd = int(mmddhh / 100 % 100)  
    hh = int(mmddhh % 100)
    dt = datetime.date(today_yy, mm, dd)
    return dt

def calc_befor24h(mmddhh) :
    hh = int(mmddhh % 100)
    dt = conv_mmddhh_to_date(mmddhh)   # date型に変換
    dt = dt - datetime.timedelta(days=1)  # 1日前
    return dt.month * 10000 + dt.day * 100 + hh

#   的中率の計算
def calc_hit_rate() : 
    global  hit_rate

    cur_mmddhh = today_mm * 10000 + today_dd * 100 + today_hh   #  現在の 日時  mmddhh 形式
    for forecast_date in  we_data.keys() :     # 予報日時
        if forecast_date > cur_mmddhh :
            break                              # 現在日時を超えたら終了
        date_str = conv_mmddhh_to_str(forecast_date)
        #print(f'{forecast_date} の天気')
        timeline_dic = we_data[forecast_date]
        if forecast_date in timeline_dic :
            act = timeline_dic[forecast_date]   #  実際の天気
            hit = 0 
            cnt = 0 
            hit24 = 0
            cnt24 = 0 
            for we in timeline_dic.values() :
                cnt += 1
                if is_rain(we) == is_rain(act) :
                    hit += 1 
            #  24時間以内の的中率
            befor24h  = calc_befor24h(forecast_date)
            for dt,we in timeline_dic.items() :
                if dt < befor24h :
                    continue 
                cnt24 += 1
                if is_rain(we) == is_rain(act) :
                    hit24 += 1 

        hitdata = {}
        hitdata['act'] = act
        hitdata['cnt'] = cnt
        hitdata['hit'] = hit
        hitdata['cnt24'] = cnt24
        hitdata['hit24'] = hit24
        hit_rate[forecast_date] = hitdata
        #print(hitdata)

    output_hit_rate()

#   的中率の表示
def output_hit_rate() :
    for forecast_date,hitdata in  hit_rate.items() :   
        cur_date = conv_mmddhh_to_date(forecast_date)  # date型
        #  7日以前は表示しない
        if cur_date < today_date - datetime.timedelta(days=7) : 
            continue 
        date_str = conv_mmddhh_to_str(forecast_date)
        act = hitdata['act']
        cnt = hitdata['cnt']
        hit = hitdata['hit']
        cnt24 = hitdata['cnt24']
        hit24 = hitdata['hit24']
        out.write(f'<tr><td>{date_str}</td><td><img src="{icon_url}{act}.png" width="20" height="15"></td>'
                  f'<td align="right">{cnt}</td><td align="right">{hit}</td>'
                  f'<td align="right">{hit/cnt*100:5.2f}</td>'
                  f'<td align="right">{cnt24}</td><td align="right">{hit24}</td>'
                  f'<td align="right">{hit24/cnt24*100:5.2f}</td></tr>')


#  雨の時 true を返す
def is_rain(we) :
    we = int(we)
    if we == 300 or we == 650 or  we == 400 or  we == 450 or  we == 800 or we == 850 :
        return True
    if we == 100 or we == 500 or  we == 550 or  we == 600 or we == 200:
        return False
    print(f'ERROR we code {we}')
    return False

def date_settings():
    global  today_date,today_mm,today_dd,today_yy,today_datetime,today_hh

    today_datetime = datetime.datetime.today()   # datetime 型
    today_date = datetime.date.today()           # date 型
    today_mm = today_date.month
    today_dd = today_date.day
    today_yy = today_date.year
    today_hh = today_datetime.hour

def conv_date_int(d) :
    i = d.month * 10000 + d.day * 100 
    return i

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%result_table%" in line :
            output_html()
            continue
        if "%calc_hit_rate%" in line :
            calc_hit_rate()
            continue
        if "%version%" in line :
            s = line.replace("%version%",version)
            out.write(s)
            continue
        if "%today%" in line :
            #today(line)
            continue
        out.write(line)

    f.close()
    out.close()

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
