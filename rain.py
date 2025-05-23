#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import locale
import datetime
import pandas as pd
import com
from datetime import date,timedelta
from ftplib import FTP_TLS

# 25/05/23 v1.02 連続雨時間解析追加
version = "1.02"

out =  ""
logf = ""
appdir = os.path.dirname(os.path.abspath(__file__))
datadir = appdir + "/data/" 
datadir_week = appdir + "/week/" 
resultfile = appdir + "/weather.htm" 
conffile = appdir + "/weather.conf"
templatefile = appdir + "/weather_templ.htm"
temperafile = appdir + "/temperature.txt"    #  実績気温データ  
dailyfile = appdir + "/dailyinfo.txt"
act_weather_file = appdir + "/actweather.txt"   #  実績天気データ  1時間ごと

df_week_rain = ""

#  週間雨時間移動平均 df_week_rain の作成
def create_df_week_rain() :
    global df_week_rain,df_daily_rain

    date_list = [] 
    rate_list = []
    is_rain_list = []   # 1時間でも雨があれば 1  全日晴れなら 0
    with open(dailyfile , encoding='utf-8') as f:
        for line in f:
            dt = line.split("\t")
            date_str = dt[0]
            rain = dt[1]
            tdate = datetime.datetime.strptime(date_str, '%y/%m/%d')            
            date_list.append(tdate)
            rate_list.append(rain)
            is_rain = 0 
            if int(rain) >= 1 :
                is_rain = 1 
            is_rain_list.append(is_rain)

    df_daily_rain = pd.DataFrame(list(zip(date_list,rate_list,is_rain_list)), columns = ['date','rain','is_rain'])
    df_daily_rain['rain'] = pd.to_numeric(df_daily_rain['rain'], errors='coerce')
    df_daily_rain['date'] = pd.to_datetime(df_daily_rain['date']) 
    df_daily_rain = df_daily_rain.set_index("date")
    seri_week_rain = df_daily_rain['rain'].rolling(7).mean()
    df_week_rain = seri_week_rain.to_frame()

#  週間雨時間移動平均グラフ
def week_rain_time_graph(out) :
    for index,row in df_week_rain.iterrows() :
        v = row['rain']
        if pd.isna(v) :
            continue 
        date_str = index.strftime('%m/%d')
        out.write(f"['{date_str}',{v}],") 

#   月別 1日平均雨時間テーブル
def monthly_rain_time(out) :
    continuous_rain()
    monthly_stats = df_daily_rain.resample('ME').agg({'rain': ['mean', 'max'],'is_rain' : 'sum'})
    #print(monthly_stats)
    for index,row in monthly_stats.iterrows() :
        ave = row['rain']['mean']
        max = row['rain']['max']
        days_rain = row['is_rain']['sum']
        date_str = index.strftime('%y/%m')
        out.write(f'<tr><td>{date_str}</td><td align="right">{ave:5.2f}</td>'
                  f'<td align="right">{max}</td><td align="right">{days_rain:4.0f}</td></tr>')

#   連続雨時間解析
def continuous_rain() :
    with open(act_weather_file , encoding='utf-8') as f:
        rain_con = 0
        prev_datestr = ""
        for line in f:
            dt = line.split("\t")
            date_str = dt[0]
            act = dt[1]
            if com.is_rain(act) :
                rain_con += 1
                prev_datestr = date_str
            else :
                if rain_con != 0 :
                    #print(f'{prev_datestr} {rain_con}')
                    rain_con = 0

