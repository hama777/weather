#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
from datetime import date,timedelta

# 25/06/20 v1.05 天気コード追加
version = "1.05"     

#  雨の時 true を返す
def is_rain(we) :
    we = int(we)
    # 雨    430  みぞれ
    if we == 300 or we == 650 or  we == 400 or  we == 450 or  we == 800 or we == 850 or we == 430 :
        return True
    # 晴れ
    if we == 100 or we == 500 or  we == 550 or  we == 600 or we == 200:
        return False
    print(f'ERROR we code {we}')
    return False

#  雨の時 true を返す
def is_rain_week(we) :
    we = int(we)       
    # 雨     311  雨のち晴れ
    # 260  曇りのち雪     411 雪のち晴   205 曇り時々雪   217 曇りのち雪   303 雨時々雪  204 曇り時々雪  400 雪  413 雪のち曇り
    if we == 102 or we == 103 or we == 106 or we == 114 or  we == 202 or we == 206 or we == 260 or\
       we == 203 or we == 214 or we == 300 or we == 301 or we == 302 or we == 313 or we == 311  or\
       we == 411 or we == 205 or we == 217 or we == 303 or we == 204 or we == 400 or we == 413 or\
       we == 882 or we == 872 or we == 852 or we == 850 :
        return True
    # 晴れ
    # 105 晴時々雪   117 晴のち雪    550 猛暑
    if we == 100 or we == 101 or we == 111 or we == 200 or  we == 201 or we == 211 or we == 105 or\
       we == 117 or we == 550 or we == 552:
        return False
    print(f'ERROR we week code {we}')
    return False

#   int の yymmddhh 形式を入力し  dd(曜日)/hh  形式の文字列を返す
def conv_mmddhh_to_str(yymmddhh,display_hh=True) :
    yy = int(yymmddhh / 1000000) + 2000
    mm = int(yymmddhh / 10000 % 100)
    dd = int(yymmddhh / 100 % 100)  
    hh = int(yymmddhh % 100)
    dt = datetime.date(yy, mm, dd)
    s = dt.strftime("%d(%a)")
    if display_hh :
        s = f'{s}/{hh:02}'
    return s 

#   int の yymmddhh 形式を入力し  yy/mm/dd hh  形式の文字列を返す
def conv_mmddhh_to_hh_str(yymmddhh) :
    yy = int(yymmddhh / 1000000) + 2000
    mm = int(yymmddhh / 10000 % 100)
    dd = int(yymmddhh / 100 % 100)  
    hh = int(yymmddhh % 100)
    dt = datetime.date(yy, mm, dd)
    s = dt.strftime("%y%m%d")
    ret = f'{s}{hh:02}'
    return ret

#   int の yymmddhh 形式を入力し  date 型の値を返す
def conv_mmddhh_to_date(yymmddhh) :
    yy = int(yymmddhh / 1000000) + 2000
    mm = int(yymmddhh / 10000 % 100)
    dd = int(yymmddhh / 100 % 100)  
    hh = int(yymmddhh % 100)
    dt = datetime.date(yy, mm, dd)
    return dt

#   int の yymmdd 形式を入力し mm/dd(aa) 形式の文字列を返す
def conv_mmdd_to_datestr(yymmdd,is_year=False) :
    yy = int(yymmdd / 10000) + 2000
    mm = int(yymmdd / 100 % 100) 
    dd = int(yymmdd % 100)  
    dt = datetime.date(yy, mm, dd)
    if is_year :
        s = dt.strftime("%y/%m/%d")
    else :
        s = dt.strftime("%m/%d(%a)")
    return s

#   int の yymmdd 形式を入力し date 型を返す
def conv_mmdd_to_date(yymmdd) :
    yy = int(yymmdd / 10000) + 2000
    mm = int(yymmdd / 100 % 100) 
    dd = int(yymmdd % 100)  
    dt = datetime.date(yy, mm, dd)
    return dt

#  int の yymmddhh 形式を入力しその1日前の yymmddhh (int) を返す
def calc_befor24h(mmddhh) :
    hh = int(mmddhh % 100)
    dt = conv_mmddhh_to_date(mmddhh)   # date型に変換
    dt = dt - datetime.timedelta(days=1)  # 1日前
    yy = dt.year - 2000
    return yy * 1000000 + dt.month * 10000 + dt.day * 100 + hh

#   yymmddhh 形式(int) から日付 dd 部分を取り出す
def get_dd_part(yymmddhh) :
    return int(yymmddhh / 100) % 10000  

#   date 型のデータを int型の yymmdd00 にして返す
def conv_date_int(d) :
    yy = d.year - 2000   #  年は西暦下2桁にする
    i = yy * 1000000 + d.month * 10000 + d.day * 100 
    return i

#   複数カラムの場合の判定
#     n  ...  何行目か     col ... 何カラム目か
#     表示しない場合(continueする場合) true を返す
def multi_col(n,col) :
    if col == 1 :
        if n > 20 :
            return True
    if col == 2 :
        if n <= 20 :
            return True
    return False

def multi_col2(n,col,limit) :
    if col == 1 :
        if n > limit :
            return True
    if col == 2 :
        if n <= limit or n > (limit * 2)  :
            return True
    if col == 3 :
        if n <= (limit * 2)  :
            return True
    return False
