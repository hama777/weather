#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import locale
import datetime
import pandas as pd
import com
import rain
from datetime import date,timedelta
from ftplib import FTP_TLS

# 25/06/05 v1.02 夏日の日数を出力する
version = "1.02"

appdir = os.path.dirname(os.path.abspath(__file__))
temperafile = appdir + "/temperature.txt"    #  実績気温データ  


#   気温のdf  
df_tempera = ""

#   日々の平均、最高、最低気温   カラム   date  avg  max min  
daily_info = ""

def read_temperature_data() :
    global df_tempera
    date_list = []
    val_list = []

    with open(temperafile) as f:
        for line in f:
            line = line.rstrip()
            data = line.split("\t")
            dt = datetime.datetime.strptime(data[0], '%y/%m/%d %H:%M')
            date_list.append(dt)
            val_list.append(int(data[1]))

    df_tempera = pd.DataFrame(list(zip(date_list,val_list)), columns = ['date','val'])

#   気温の日々の平均値、最高値、最低値、標準偏差を求める
#   気温の7日移動平均  df_week_tempera  作成
def create_temperature_info() :
    global daily_info,df_week_tempera
    seri_tmp  = df_tempera.groupby(df_tempera['date'].dt.date)['val'].mean()
    daily_avg = seri_tmp.rename('avg')
    seri_tmp = df_tempera.groupby(df_tempera['date'].dt.date)['val'].max()
    daily_max = seri_tmp.rename('max')
    seri_tmp = df_tempera.groupby(df_tempera['date'].dt.date)['val'].min()
    daily_min = seri_tmp.rename('min')
    seri_tmp = df_tempera.groupby(df_tempera['date'].dt.date)['val'].std()
    daily_std = seri_tmp.rename('std')
    daily_info = pd.merge(daily_avg,daily_max,on='date')
    daily_info = pd.merge(daily_info,daily_min,on='date')
    daily_info = pd.merge(daily_info,daily_std,on='date')
    seri_week_tempera = daily_info['avg'].rolling(7).mean()
    df_week_tempera = seri_week_tempera.to_frame()

    daily_info = daily_info.reset_index()   # すでに date が index になっているので戻す
    daily_info['date'] = pd.to_datetime(daily_info['date'])  # date を datetime 型にする
    daily_info = daily_info.set_index('date')    #  date をindexにする
    #print(daily_info.columns)  
    #print(daily_info)

#   日別気温データ
#   気温の日々の平均値、最高値、最低値の表示
def temperature_info(out,col) :
    n = 0 
    for index,row in daily_info.tail(40).iterrows() :
        n += 1
        if com.multi_col(n,col) :
            continue 
        date_str = index.strftime('%m/%d(%a)')
        out.write(f"<tr><td>{date_str}</td><td align='right'>{row['avg']:4.2f}</td>"
                  f"<td align='right'>{row['max']:4.0f}</td>"
                  f"<td align='right'>{row['min']:4.0f}</td>"
                  f"<td align='right'>{row['std']:4.2f}</td></tr>\n")


#   日別気温データの過去最高値、最低値を表示
def min_max_temperature(out) :
    min_max_temperature_com(out,daily_info)

#   過去30日間の日別気温データの過去最高値、最低値を表示
def min_max_temperature_30days(out) :
    df_30 = daily_info.tail(30)
    min_max_temperature_com(out,df_30)

#   日別気温データの過去最高値、最低値を取得
def min_max_temperature_com(out,arg_df) :
    item_list = ['avg','max','min'] 
    item_name = {'avg' : '日平均気温','max' : '日最高気温','min' :'日最低気温'}
    aggmax = {}
    aggmax_date = {}
    aggmin = {}
    aggmin_date = {}
    for item in item_list :
        tdate = arg_df[item].idxmax()
        aggmax_date[item] = tdate.strftime('%m/%d(%a)')
        aggmax[item] = arg_df.loc[tdate,item ]

        tdate = arg_df[item].idxmin()
        aggmin_date[item] = tdate.strftime('%m/%d(%a)')
        aggmin[item] = arg_df.loc[tdate,item ]

    for item in item_list :
        out.write(f'<tr><td>{item_name[item]}</td>')
        out.write(f'<td align="right">{aggmax[item]:4.2f}</td><td>{aggmax_date[item]}</td>'
                  f'<td align="right">{aggmin[item]:4.2f}</td><td>{aggmin_date[item]}</td></tr>\n')

def monthly_tempera(out) :
    # 月ごとに avg max min の 平均値、最大値、最小値、夏日日数 を求める
    summerday_limit = [25,30,35]

    monthly_summary = daily_info.resample('ME').agg({
        'avg': ['mean', 'max', 'min','std'],
        'max': [ 'mean', 'max', 'min'],
        'min': [ 'mean', 'max', 'min']
    })    
    for lim in summerday_limit :
        count_summerday = (daily_info['max'] >= lim).resample('ME').sum().astype(int)
        col_name = f'summerday_{lim}'
        count_summerday.name = ('avg', col_name)  # MultiIndexの列名に合わせる
        monthly_summary[('avg', col_name)] = count_summerday

    for index,row in monthly_summary.iterrows() :
        date_str = index.strftime('%y/%m')
        out.write(f'<tr><td>{date_str}</td><td align="right">{row["avg"]["mean"]:4.2f}</td>'
                  f'<td align="right">{row["avg"]["max"]:4.2f}</td>'
                  f'<td align="right">{row["avg"]["min"]:4.2f}</td>'
                  f'<td align="right">{row["max"]["max"]}</td>'
                  f'<td align="right">{row["min"]["min"]}</td>'
                  f'<td align="right">{row["avg"]["std"]:4.2f}</td>'
                  f'<td align="right">{row["avg"]["summerday_25"]:3.0f}</td>'
                  f'<td align="right">{row["avg"]["summerday_30"]:3.0f}</td>'
                  f'<td align="right">{row["avg"]["summerday_35"]:3.0f}</td></tr>\n')

#   気温グラフ   時間ごと
def tempera_graph(out) :
    df = df_tempera.tail(336)   # 2週間分  24 * 14
    for _,row in df.iterrows() :
        date_str = row['date'].strftime('%d %H')
        v = row['val']
        out.write(f"['{date_str}',{v}],") 

#   気温グラフ   日ごと
def tempera_graph_daily(out) :
    for index,row in daily_info.iterrows() :
        date_str = index.strftime('%m/%d')
        v = row['avg']
        out.write(f"['{date_str}',{v}],") 

#   気温グラフ   7日移動平均
def tempera_graph_week(out) :
    for index,row in df_week_tempera.iterrows() :
        v = row['avg']
        if pd.isna(v) :
            continue 
        date_str = index.strftime('%m/%d')
        out.write(f"['{date_str}',{v}],") 
