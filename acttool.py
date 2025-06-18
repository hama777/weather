#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
#import locale
import datetime
#import pandas as pd
import com
#import rain
#import tempera
from datetime import date,timedelta
from ftplib import FTP_TLS

# 1時間ごと実績天気データファイルを作成するツール
# 25/06/17 v1.00 新規
version = "1.00"

appdir = os.path.dirname(os.path.abspath(__file__))
act_weather_file2 = appdir + "/actweather2.txt"   #  実績天気データ  1時間ごと  暫定
datadir = appdir + "/data/" 
olddatadir = appdir + "/old/data/" 

def main_proc() :
    create_act_weather_file()

#  過去からのファイルを読んで 実際の天気の情報をファイルに出力する  作成中
def create_act_weather_file() :
    actf = open(act_weather_file2,'w')
    dir_path = olddatadir
    datafile_list = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]
    for fname in datafile_list :
        read_one_hour(dir_path + fname,actf)

    dir_path = datadir
    datafile_list = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]
    for fname in datafile_list :
        read_one_hour(dir_path + fname,actf)
    actf.close()

def read_one_hour(datafile,actf) :
    f = open(datafile , 'r')
    header  = f.readline().strip()
    hh = header.split()
    date_str = hh[0]
    start_hh = int(hh[1])   
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    start_date = datetime.date(dt.year, dt.month, dt.day) # データの開始日付 date型
    start_date_int = com.conv_date_int(start_date)            # データの開始日付 yymmddhh の int型 キーとして使用
    start_date_int += start_hh

    body  = f.readline().strip()
    we_data = body.split(",")[0]        #  we_list は1時間ごとの天気
    actf.write(f'{start_date_int}\t{we_data}\n') 
    f.close()

# -------------------------------------------------------------
main_proc()

