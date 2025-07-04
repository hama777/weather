#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import locale
import datetime
import pandas as pd
import com
from datetime import date,timedelta
from ftplib import FTP_TLS

# 25/06/25 v1.11 連続晴時間Topを表示
version = "1.11"

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
    #continuous_fine_rain()
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
def continuous_fine_rain() :
    global rain_date_list,rain_con_list
    global fine_date_list,fine_con_list
    global cur_continuous_data 
    global df_cont_rain,df_cont_fine
    cur_continuous_data = {}    # 現在の連続天気情報   key date , count , rain(雨の時 1)  
    rain_con = 0
    fine_con = 0 
    rain_date_list = []
    rain_con_list = []
    fine_date_list = []
    fine_con_list = []
    prev_datestr = ""
    date_str = ""
    with open(act_weather_file , encoding='utf-8') as f:
        for line in f:
            dt = line.split("\t")
            prev_datestr = date_str
            date_str = dt[0]
            act = dt[1]
            if com.is_rain(act) :
                if fine_con != 0 :
                    fine_date_list.append(prev_datestr)
                    fine_con_list.append(fine_con)
                    fine_con = 0 
                rain_con += 1
            else :
                if rain_con != 0 :
                    rain_date_list.append(prev_datestr)
                    rain_con_list.append(rain_con)
                    rain_con = 0
                fine_con += 1

    if rain_con != 0 :
        cur_continuous_data['date'] = date_str
        cur_continuous_data['count'] = rain_con
        cur_continuous_data['rain'] = 1
        rain_date_list.append(date_str)
        rain_con_list.append(rain_con)

    if fine_con != 0 :
        cur_continuous_data['date'] = date_str
        cur_continuous_data['count'] = fine_con
        cur_continuous_data['rain'] = 0
        fine_date_list.append(date_str)
        fine_con_list.append(fine_con)

    #print(cur_continuous_data)
    #print(rain_date_list,rain_con_list)
    #print(fine_date_list,fine_con_list)

    df_cont_rain = pd.DataFrame(list(zip(rain_date_list,rain_con_list)), columns = ['yymmddhh','cont'])
    df_cont_fine = pd.DataFrame(list(zip(fine_date_list,fine_con_list)), columns = ['yymmddhh','cont'])
    #print(df_cont_rain)

def continuous_rain(out) :
    last = 20    # 直近、n件のみ表示する
    for rdate , rtime in zip(rain_date_list[-last:],rain_con_list[-last:]) :
        # if rtime <= 3 :   #  連続3時間以内は無視
        #     continue
        yymmddhh  = int(rdate)
        dt = com.conv_mmddhh_to_date(yymmddhh)
        hh = yymmddhh % 100
        date_str = dt.strftime('%m/%d (%a)')
        out.write(f'<tr><td>{date_str} {hh:02}時</td><td align="right">{rtime}</td></tr>\n')

def top_continuous_rain(out) :
    df_top = df_cont_rain.sort_values('cont',ascending=False)
    top_continuous_com(out,df_top) 

def top_continuous_fine(out) :
    df_top = df_cont_fine.sort_values('cont',ascending=False)
    top_continuous_com(out,df_top) 

def top_continuous_com(out,df_top) :
    for index,row in df_top.head(5).iterrows() :
        yymmddhh  = int(row['yymmddhh'])
        dt = com.conv_mmddhh_to_date(yymmddhh)
        hh = yymmddhh % 100
        date_str = dt.strftime('%m/%d (%a)')
        count = row['cont']
        days = count // 24
        fine_hh = count % 24

        out.write(f'<tr><td>{date_str} {hh:02}時</td><td align="right">{count}({days:2}日{fine_hh:02}時間)</td></tr>\n')

def continuous_fine(out) :
    last = 20
    for rdate , rtime in zip(fine_date_list[-last:],fine_con_list[-last:]) :
        # if rtime <= 24 :  #  連続24時間以内は無視
        #     continue
        yymmddhh  = int(rdate)
        dt = com.conv_mmddhh_to_date(yymmddhh)
        hh = yymmddhh % 100
        date_str = dt.strftime('%m/%d (%a)')
        days = rtime // 24
        fine_hh = rtime % 24
        out.write(f'<tr><td>{date_str} {hh:02}時</td><td align="right">{rtime}({days}日{fine_hh:02}時間)</td></tr>\n')

def cur_continuous(out) :
    if cur_continuous_data['rain'] == 0 :
        s = "連続晴情報 "
    else :
        s = "連続雨情報 "
    yymmddhh  = int(cur_continuous_data['date'])
    dt = com.conv_mmddhh_to_date(yymmddhh)
    hh = yymmddhh % 100
    date_str = dt.strftime('%m/%d (%a)')
    out.write(f"{s} {cur_continuous_data['count']} 時間 {date_str} {hh}時 現在\n")

