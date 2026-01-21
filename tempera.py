#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import locale
import datetime
import pandas as pd
import com
#import rain
from datetime import date,timedelta
from ftplib import FTP_TLS

# 26/01/21 v1.20 前週気温差表示廃止
version = "1.20"

# TODO: today_date  yesterday を共通化する

appdir = os.path.dirname(os.path.abspath(__file__))
temperafile = appdir + "/temperature.txt"    #  実績気温データ  

#   気温のdf  
df_tempera = ""

#  日々の気温データ df カラム date avg(日平均) max min  diff(前日差)  day_diff(1日寒暖差)
daily_info = ""

temperature_info_col = 0

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
            val_list.append(float(data[1]))

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
    diff_list = calc_differencr()
    daily_info['diff'] = diff_list
    day_diff = calc_day_diff()
    daily_info['day_diff'] = day_diff

def ranking_diff_top(out) :
    df_diff_top = daily_info.sort_values('diff',ascending=False).head(10)
    ranking_diff_com(df_diff_top,out)

def ranking_diff_low(out) :
    df_diff_top = daily_info.sort_values('diff',ascending=True).head(10)
    ranking_diff_com(df_diff_top,out)

def ranking_diff_com(arg_df,out) :
    today_date = datetime.date.today()  
    yesterday = today_date - timedelta(days=1)

    i = 0 
    for index,row in arg_df.iterrows() :
        i += 1
        date_str = index.strftime('%y/%m/%d(%a)')
        if index.date() == today_date :
            date_str = f'<span class=red>{date_str}</span>'
        if index.date() == yesterday :
            date_str = f'<span class=blue>{date_str}</span>'
        out.write(f'<tr><td align=right>{i}</td><td>{date_str}</td><td align=right>{row["diff"]:4.2f}</td></tr>\n')

#   前日との気温差を計算
def calc_differencr() :
    i = 0 
    prev = 99
    diff_list = []
    for index,row in daily_info.iterrows() :
        i += 1 
        if i == 1 : 
            prev = row['avg']
            diff_list.append(0)
            continue
        diff = row['avg'] - prev
        diff_list.append(diff)
        prev = row['avg']

    return diff_list 

#   1日の気温差を計算
def calc_day_diff() :
    day_diff_list = []
    for index,row in daily_info.iterrows() :
        diff = row['max'] - row['min']
        day_diff_list.append(diff)

    return day_diff_list 

#   日別気温データ
#   気温の日々の平均値、最高値、最低値の表示
def temperature_info(out) :
    global temperature_info_col
    temperature_info_col += 1 
    n = 0 
    for index,row in daily_info.tail(40).iterrows() :
        n += 1
        if com.multi_col(n,temperature_info_col) :
            continue 
        date_str = index.strftime('%m/%d(%a)')
        diff = row['diff']
        diff_str = f"{diff:4.2f}"
        if diff < 0 :
            diff_str = f"<span class=red>{diff_str}</span>"

        out.write(f"<tr><td>{date_str}</td><td align='right'>{row['avg']:4.2f}</td>"
                  f"<td align='right'>{row['max']:4.1f}</td>"
                  f"<td align='right'>{row['min']:4.1f}</td>"
                  f"<td align='right'>{row['std']:4.2f}</td>"
                  f"<td align='right'>{diff_str}</td>"
                  f"<td align='right'>{row['day_diff']:4.1f}</td></tr>\n")


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
        aggmax_date[item] = tdate.strftime('%y/%m/%d(%a)')
        aggmax[item] = arg_df.loc[tdate,item ]

        tdate = arg_df[item].idxmin()
        aggmin_date[item] = tdate.strftime('%y/%m/%d(%a)')
        aggmin[item] = arg_df.loc[tdate,item ]

    for item in item_list :
        out.write(f'<tr><td>{item_name[item]}</td>')
        out.write(f'<td align="right">{aggmax[item]:4.2f}</td><td>{aggmax_date[item]}</td>'
                  f'<td align="right">{aggmin[item]:4.2f}</td><td>{aggmin_date[item]}</td></tr>\n')

#   7日移動平均テーブル
def weekly_tempera_table(out) :
    df_week_tempera['avg_1_before'] = df_week_tempera['avg'].shift(1)
    df_week_tempera['avg_7_before'] = df_week_tempera['avg'].shift(7)
    df_week_tempera['avg_14_before'] = df_week_tempera['avg'].shift(14)
    for index,row in df_week_tempera.tail(15).iterrows() :
        v = row['avg']
        v1 = row['avg_1_before']
        v7 = row['avg_7_before']
        v14 = row['avg_14_before']

        if pd.isna(v) :
            continue 
        date_str = index.strftime('%m/%d(%a)')
        diff1 = float_to_color_str(v - v1)
        diff7 = float_to_color_str(v - v7)
        diff14 = float_to_color_str(v - v14)
        out.write(f"<tr><td>{date_str}</td><td align='right'>{v:4.2f}</td>"
                  f"<td align='right'>{diff1}</td><td align='right'>{diff7}</td>"
                  f"<td align='right'>{diff14}</td></tr>\n")         

def float_to_color_str(f) :
    if f < 0 :
        s = f'<span class=red>{f:4.2f}</span>'
    else :
        s = f'{f:4.2f}'
    return s

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

    # 1年前の平均気温との差分を取る
    monthly_summary['year_diff'] = (
        monthly_summary[('avg','mean')]
        - monthly_summary[('avg','mean')].shift(12)
    )
    for index,row in monthly_summary.iterrows() :
        date_str = index.strftime('%y/%m')
        year_diff = row[("year_diff","")]   # muliindex なので 全部 flat化したほうがよいかも
        if pd.isna(year_diff) :
            year_diff_str = ""
        else :
            year_diff_str = f'{year_diff:4.2f}'

        out.write(f'<tr><td>{date_str}</td><td align="right">{row["avg"]["mean"]:4.2f}</td>'
                  f'<td align="right">{year_diff_str}</td>'
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
    for index,row in daily_info.tail(180).iterrows() :
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

# def output_tempera_week(out) :
#     last_value = df_week_tempera.iloc[-1]['avg']
#     out.write(f"{last_value:5.2f}\n") 

# def output_tempera_week_diff(out) :
#     last_value = df_week_tempera.iloc[-1]['avg']
#     last_week_value = df_week_tempera.iloc[-8]['avg']
#     diff = last_value - last_week_value
#     out.write(f"{diff:5.2f}\n") 

#   平均気温ランキング
def ranking_ave_tempera(out) :
    df_top = daily_info.sort_values('avg',ascending=False)
    ranking_tempera_com(df_top.head(10),'avg',out)

def ranking_max_tempera(out) :
    df_max = daily_info.sort_values('max',ascending=False)
    ranking_tempera_com(df_max.head(10),'max',out)

def ranking_min_tempera(out) :
    df_min = daily_info.sort_values('min',ascending=False)
    ranking_tempera_com(df_min.head(10),'min',out)

def ranking_ave_tempera_low(out) :
    df_top = daily_info.sort_values('avg',ascending=True)
    ranking_tempera_com(df_top.head(10),'avg',out)

def ranking_max_tempera_low(out) :
    df_max = daily_info.sort_values('max',ascending=True)
    ranking_tempera_com(df_max.head(10),'max',out)

def ranking_min_tempera_low(out) :
    df_min = daily_info.sort_values('min',ascending=True)
    ranking_tempera_com(df_min.head(10),'min',out)

def ranking_daily_diff(out) :
    df_top = daily_info.sort_values('day_diff',ascending=False)
    ranking_tempera_com(df_top.head(10),'day_diff',out)

def ranking_tempera_com(df,col,out) :
    i = 0 
    today_date = datetime.date.today()  
    yesterday = today_date - timedelta(days=1)
    for index,row in df.iterrows() :
        i += 1
        date_str = index.strftime('%y/%m/%d (%a)')
        #print(index,today_date)
        if index.date() == today_date :
            date_str = f'<span class=red>{date_str}</span>'
        if index.date() == yesterday :
            date_str = f'<span class=blue>{date_str}</span>'
        val = row[col]
        out.write(f'<tr><td align="right">{i}</td><td>{date_str}</td><td align="right">{val:5.2f}</td></tr>\n')
