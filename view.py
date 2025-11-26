#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import locale
import datetime
import pandas as pd
import com
import rain
import tempera
from datetime import date,timedelta
from ftplib import FTP_TLS

# 25/11/26 v1.67 週平均気温テーブル追加
version = "1.67"

out =  ""
logf = ""
appdir = os.path.dirname(os.path.abspath(__file__))
datadir = appdir + "/data/" 
olddatadir = appdir + "/old/data/" 
datadir_week = appdir + "/week/" 
resultfile = appdir + "/weather.htm" 
conffile = appdir + "/weather.conf"
templatefile = appdir + "/weather_templ.htm"
temperafile = appdir + "/temperature.txt"    #  実績気温データ  
dailyfile = appdir + "/dailyinfo.txt"

res = ""
week_data_interval = 6   #  週間天気で何時間起きにデータを採取するか
rain_threshold = 4       #  1日で何時間雨の場合、 雨 と判定するか

#    we_data  データ形式
#    we_data = {
#        予報日時 : {発表日時 : 天気, 発表日時 : 天気, ... },
#        予報日時 : {発表日時 : 天気, 発表日時 : 天気, ... }
#    }
#      予報日時 予報天気の日時  yymmddhh をintとして持つ
#      発表日時 はその予報が発表された日時  yymmddhh をintとして持つ  ファイルの先頭に記録されている  
#      予報天気 int   100 晴れ  200  曇り  300 以上  雨
#    例  
#    発表日時      予報日時     予報天気   予報日時     予報天気
#    10/01 01:00  10/01 12:00  100       10/01 13:00     200   ... この1行が 1ファイル
#    10/01 02:00  10/01 12:00  100       10/01 13:00     100 
#    10/01 03:00  10/01 12:00  100       10/01 13:00     300
#    以下のデータになる
#    24100112  {24100101:100 , 24100102 : 100, 24100103 : 200, ....}
#    24100113  {24100101:200 , 24100102 : 100, 24100103 : 300, ....}
we_data = {}

#    week_data  週間天気の情報   データ形式
#    week_data = {
#        予報日時 : {発表日時 : 天気, 発表日時 : 天気, ... },
#        予報日時 : {発表日時 : 天気, 発表日時 : 天気, ... }
#    }
#      発表日時  yymmddhh をintとして持つ   予報日  yymmdd00 をintとして持つ
week_data = {}

#  天気コード
#   1時間天気
#     100 500 550 600  晴れ  200  曇り  300  雨  650 小雨  400 450 雪   250  曇り 雪  800 曇り雷 850 大雨
#  週間天気
#   100 晴れ  101 晴れのち曇り 102 103 106  晴れのち雨  200 曇り 201 曇りのち晴 202 曇りのち雨  260 曇りのち雪
#   300 雨 301 雨のち晴れ  302 雨のち曇り   400 雪

#  天気アイコンのURL は  https://weathernews.jp/onebox/img/wxicon/{天気コード}.png
icon_url = "https://weathernews.jp/onebox/img/wxicon/"

#   hit_rate 的中率のデータ
#   hit_rate 辞書  { yymmddhh : hitdata }
#      hitdata 辞書 { act : 実際の天気(int) , cnt : 総件数 , hit : ヒット件数}
hit_rate = {}

#   1日ごとの的中率データ
#   daily_rate  辞書   { yymmdd : hitdata }
#      hitdata 辞書 {  cnt : 総件数 , hit : ヒット件数}
daily_rate = {}

#   週間天気予報の的中率データ
#   week_rate  辞書   { yymmdd : hitdata }
#      hitdata 辞書 {  cnt : 総件数 , hit : ヒット件数}
week_rate = {}

#   気温のdf  
df_tempera = ""

#   日々の平均、最高、最低気温   カラム   date  avg  max min  
daily_info = ""

#df_week_rain  = ""  #  1日雨時間の7日間移動平均   date(index)  rain

def main_proc() :
    locale.setlocale(locale.LC_TIME, '')
    date_settings()
    read_config()
    tempera.read_temperature_data()

    dir_path = datadir
    datafile_list = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]
    for fname in datafile_list :
        read_data(fname)

    dir_path = datadir_week
    datafile_list = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]
    for fname in datafile_list :
        read_data_week(fname)

    calc_hit_rate()
    calc_hit_rate_week()    
    tempera.create_temperature_info()
    rain.preprocess()  
    parse_template()
    ftp_upload()
    daily_info_output()

def read_data(fname) : 
    global start_date,start_hh,we_list

    datafile = datadir + fname
    f = open(datafile , 'r')
    header  = f.readline().strip()
    hh = header.split()
    date_str = hh[0]
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    start_date = datetime.date(dt.year, dt.month, dt.day) # データの開始日付 date型
    start_date_int = com.conv_date_int(start_date)            # データの開始日付 yymmddhh の int型 キーとして使用
    start_hh = int(hh[1])            # データの開始時刻

    body  = f.readline().strip()
    we_list = body.split(",")        #  we_list は1時間ごとの天気
    f.close()

    pub_date = start_date_int + start_hh   #  発表日時 int  yymmddhh  we_data のvalの辞書のキー として使用
    cur_hh = start_hh                # 以下のループで現在の時刻として使用  int 型
    cur_date = start_date            # 以下のループで現在の日付として使用  date 型

    for we in we_list :
        k = com.conv_date_int(cur_date) + cur_hh    #  we_data の key
        
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

#   週間天気予報データの読み込み
def read_data_week(fname) : 

    datafile = datadir_week + fname
    f = open(datafile , 'r')
    header  = f.readline().strip()
    hh = header.split()
    date_str = hh[0]
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    start_date = datetime.date(dt.year, dt.month, dt.day) # データの開始日付 date型
    start_date_int = com.conv_date_int(start_date)            # データの開始日付 yymmddhh の int型 キーとして使用
    start_hh = int(hh[1])            # データの開始時刻

    body  = f.readline().strip()
    week_list = body.split(",")        #  week_list は1日ごとの天気
    f.close()

    pub_date = start_date_int + start_hh   #  発表日時 int  yymmddhh  we_data のvalの辞書のキー として使用
    cur_date = start_date            # 以下のループで現在の日付として使用  date 型

    #print(week_list)
    for we in week_list :
        k = com.conv_date_int(cur_date)     #  we_data の key
        
        if k in week_data :       # すでにキーがある場合はそのキーに対応する辞書に追加する
            val = week_data[k]    # そのキーに対応する辞書
            val[pub_date] = we    # そのキーに対応する辞書 に天気を追加
            week_data[k] = val    # we_data にどの辞書を再格納
        else :
            timeline_dic = {}   # キーがない場合は辞書を作成し、we_data の値として格納する
            timeline_dic[pub_date] = we
            week_data[k] = timeline_dic
        cur_date +=  datetime.timedelta(days=1)
    #print(week_data)


#   時間天気予報の表示
def hour_forecast() :

    display_start_day = 1   #  display_start_day 前から表示を開始する 
    display_start_hh = 0    #  表示を開始する時刻   1日前の0時から表示する
    out.write('<thead><tr><th>予報日時</th>\n')
    cur_date = today_date - datetime.timedelta(days=display_start_day)    # 予報は今日のdisplay_start_day日前から
    #cur_hh = start_hh        
    cur_hh = display_start_hh        
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
        yymmdd = int(forecast_date / 100)
        if yymmdd < today_yy * 10000 + today_mm * 100 + today_dd :  # 昨日以前の情報は出さない
            continue 

        forecast_str = com.conv_mmddhh_to_str(forecast_date)
        out.write(f'<tr><td>{forecast_str}</td>\n')
        timeline_dic = we_data[forecast_date]
        cur_date = today_date - datetime.timedelta(days=display_start_day)    # 予報は今日のdisplay_start_day日前から
        #cur_hh = start_hh
        cur_hh = display_start_hh
        while True :
            k = com.conv_date_int(cur_date) + cur_hh    # k 発表日時
            if k in  timeline_dic :
                we = timeline_dic[k]
                out.write(f'<td><img src="{icon_url}{we}.png" width="20" height="15"></td>\n')
            else :
                out.write("<td>--</td>")
            cur_hh += 1
            if cur_hh == 24 :
                cur_hh = 0
                cur_date +=  datetime.timedelta(days=1)
            if cur_date > start_date  : # 
                break
        out.write("</tr>\n")
    out.write("</tbody>\n")

#   週間天気予報の表示
def week_forecast() :

    out.write('<thead><tr><th>予報日時</th>\n')
    cur_date = today_date - datetime.timedelta(days=10)    # 予報は今日の10日前から
    cur_hh = 0        
    #  テーブルヘッダ出力
    while True :
        out.write(f'<th>{cur_date.day}<br>{cur_hh:02}</th>')
        cur_hh += week_data_interval
        if cur_hh == 24 :
            cur_hh = 0
            cur_date +=  datetime.timedelta(days=1)
        if cur_date > start_date  : # 
            break
    out.write("</tr>\n</thead>\n")

    out.write("<tbody>\n")
    for forecast_date in  week_data.keys() :     # 予報日時
        yymmdd = int(forecast_date / 100)
        if yymmdd < today_yy * 10000 + today_mm * 100 + today_dd :  # 昨日以前の情報は出さない
            continue 

        forecast_str = com.conv_mmddhh_to_str(forecast_date,display_hh=False)
        out.write(f'<tr><td>{forecast_str}</td>\n')
        timeline_dic = week_data[forecast_date]
        cur_date = today_date - datetime.timedelta(days=10)    # 予報は今日の10日前から
        cur_hh = 0
        while True :
            k = com.conv_date_int(cur_date) + cur_hh    # k 発表日時
            if k in  timeline_dic :
                we = timeline_dic[k]
                out.write(f'<td><img src="{icon_url}{we}.png" width="20" height="15"></td>\n')
            else :
                out.write("<td>--</td>")
            cur_hh += week_data_interval
            if cur_hh == 24 :
                cur_hh = 0
                cur_date +=  datetime.timedelta(days=1)
            if cur_date > start_date  : # 
                break
        out.write("</tr>\n")
    out.write("</tbody>\n")

#   的中率の計算
#      hit_rate  辞書   キー  予報日時  値  hitdata
#      hitdata   辞書   キー  act 実際の天気(天気コード)  cnt 予報回数  hit 的中回数  hit24  24時間用  cnt24  24時間用
def calc_hit_rate() : 
    global  hit_rate,daily_rate

    cur_mmddhh = today_yymmddhh   #  現在の 日時  yymmddhh 形式
    cur_dd = 0 
    daily_cnt = 0     # 1日ごとの集計に使う
    daily_hit = 0
    daily_rain = 0 
    for forecast_date in  we_data.keys() :     # 予報日時
        if forecast_date > cur_mmddhh :
            break                              # 現在日時を超えたら終了
        date_str = com.conv_mmddhh_to_str(forecast_date)
        dd = com.get_dd_part(forecast_date)         # 日付部分
        timeline_dic = we_data[forecast_date]
        if forecast_date in timeline_dic :
            act = timeline_dic[forecast_date]   #  実際の天気
            if com.is_rain(act) :
                daily_rain += 1    #  1日のうち 雨の回数をカウント 
            hit = 0 
            cnt = 0 
            hit24 = 0
            cnt24 = 0 
            for we in timeline_dic.values() :
                cnt += 1
                if com.is_rain(we) == com.is_rain(act) :
                    hit += 1 

            #  24時間以内の的中率
            befor24h  = com.calc_befor24h(forecast_date)
            for dt,we in timeline_dic.items() :
                if dt < befor24h :
                    continue 
                cnt24 += 1
                if com.is_rain(we) == com.is_rain(act) :
                    hit24 += 1 

        hitdata = {}
        hitdata['act'] = act
        hitdata['cnt'] = cnt
        hitdata['hit'] = hit
        hitdata['cnt24'] = cnt24
        hitdata['hit24'] = hit24
        hit_rate[forecast_date] = hitdata

        #  1日データの集計
        if dd != cur_dd :    # 日が変わったら1日データを追加する
            befor = com.calc_befor24h(forecast_date)   # forecast_date は新しい日になっているので1日前を取得
            add_daily_data(daily_cnt,daily_hit,befor,daily_rain)
            daily_cnt = 0 
            daily_hit = 0
            daily_rain = 0
            cur_dd = dd

        daily_cnt += cnt
        daily_hit += hit

    #  最後に当日分のデータを追加する
    add_daily_data(daily_cnt,daily_hit,forecast_date,daily_rain)

#   1日データの追加
def add_daily_data(cnt,hit,dd,act) :
    global daily_rate

    daily_hitdata = {}
    daily_hitdata['cnt'] = cnt
    daily_hitdata['hit'] = hit
    daily_hitdata['act'] = act
    daily_rate[int(dd/100)] = daily_hitdata

#   時間的中率の表示
def output_hit_rate(col) :
    n = 0 
    for forecast_date,hitdata in  hit_rate.items() :   
        cur_date = com.conv_mmddhh_to_date(forecast_date)  # date型
        #  7日以前は表示しない
        if cur_date < today_date - datetime.timedelta(days=6) : 
            continue 

        n += 1
        if com.multi_col2(n,col,56) :
            continue
        date_str = com.conv_mmddhh_to_str(forecast_date)
        act = hitdata['act']
        cnt = hitdata['cnt']
        hit = hitdata['hit']
        cnt24 = hitdata['cnt24']
        hit24 = hitdata['hit24']
        out.write(f'<tr><td>{date_str}</td><td><img src="{icon_url}{act}.png" width="20" height="15"></td>'
                  f'<td align="right">{hit/cnt*100:5.2f}</td>'
                  f'<td align="right">{hit24/cnt24*100:5.2f}</td></tr>')

#   日的中率の表示
def daily_hit_rate(col) :
    n = 0 
    for forecast_date,hitdata in  daily_rate.items() :   
        cur_date = com.conv_mmddhh_to_date(forecast_date*100)  # forecast_date は yymmdd のため *100 して yymmddhh 形式にする
        if cur_date < today_date - datetime.timedelta(days=39) : 
            continue 
        n += 1
        if com.multi_col(n,col) :
            continue
                
        date_str = com.conv_mmdd_to_datestr(forecast_date)
        cnt = hitdata['cnt']
        hit = hitdata['hit']
        act = hitdata['act']
        if cnt != 0 :
            r = hit/cnt*100 
        else :
            r = 0 
        img = f'{icon_url}100.png'   #  晴れのアイコン 
        if act >= 1 :    # 1日で1回でも雨があれば 雨のアイコンにする
            img = f'{icon_url}300.png'   #  雨のアイコン

        out.write(f'<tr><td>{date_str}</td><td><img src="{img}" width="20" height="15"></td>'
                  f'<td align="right">{act}</td><td align="right">{cnt}</td><td align="right">{hit}</td>'
                  f'<td align="right">{r:5.2f}</td></tr>')


#   日毎の情報をファイルに出力
def daily_info_output() :
    init_flg = 0           #  1 の時、全データを出力する(初期設定用)。  0 の時、追加分だけ。
    with open(dailyfile , encoding='utf-8') as f:
        for line in f:
            continue
    
    d = line.split('\t')
    dt = datetime.datetime.strptime(d[0], '%y/%m/%d')
    lastdate = dt.date()   #  最終データの日付  date型

    if init_flg == 1 :
        dailyf = open(dailyfile , 'w', encoding='utf-8')
    else :
        dailyf = open(dailyfile , 'a', encoding='utf-8')
    for forecast_date,hitdata in  daily_rate.items() :   
                
        fdate = com.conv_mmdd_to_date(forecast_date)    # date型
        if init_flg == 0 and fdate <= lastdate :   # 最終データより前のデータは出力しない
            continue
        if fdate >= today_date :  # 今日のデータは出力しない
           break 
        date_str = com.conv_mmdd_to_datestr(forecast_date,is_year=True)
        cnt = hitdata['cnt']
        hit = hitdata['hit']
        act = hitdata['act']
        s = f'{date_str}\t{act}\t{cnt}\t{hit}\n'
        dailyf.write(s)
    
    dailyf.close()

#   週間予報的中率の計算
def calc_hit_rate_week() : 
    global week_rate

    for forecast_date in  week_data.keys() :     # 予報日時
        yymmdd = int(forecast_date / 100)
        if yymmdd >= today_yy * 10000 + today_mm * 100 + today_dd :  # 現在日(を含む)を超えたら終了
            break

        timeline_dic = week_data[forecast_date]
        try:
            daily_hitdata = daily_rate[yymmdd]
        except KeyError:
            break
        rain_time = daily_hitdata['act']   # 1日で何時間雨か
        act_is_rain = is_rain_day(rain_time)   # 雨の時  true

        hit = 0 
        cnt = 0 
        for we in timeline_dic.values() :
            cnt += 1
            if com.is_rain_week(we) == act_is_rain :
                hit += 1 

        hitdata = {} 
        hitdata['cnt'] = cnt
        hitdata['hit'] = hit
        hitdata['rain_time'] = rain_time
        hitdata['act'] = act_is_rain
        week_rate[yymmdd] = hitdata

#  週間天気予報 的中率の表示
def output_week_hit_rate(col) :
    n = 0 
    week_rate_last = dict(list(week_rate.items())[-40:])  #  上限00件
    for yymmdd, hitdata in week_rate_last.items() :
        n += 1
        if com.multi_col(n,col) :
            continue

        date_str = com.conv_mmdd_to_datestr(yymmdd)
        cnt = hitdata['cnt']
        hit = hitdata['hit']
        rain_time = hitdata['rain_time']
        act = hitdata['act']
        if cnt != 0 :
            r = hit/cnt*100 
        else :
            r = 0 
        img = f'{icon_url}100.png'   #  晴れのアイコン 
        if act :
            img = f'{icon_url}300.png'   #  晴れのアイコン 

        out.write(f'<tr><td>{date_str}</td><td><img src="{img}" width="20" height="15"></td>'
                  f'<td align="right">{rain_time}</td><td align="right">{cnt}</td><td align="right">{hit}</td>'
                  f'<td align="right">{r:5.2f}</td></tr>')

#  1日のうち rain_threshold 時間以上雨の場合、 true を返す
def is_rain_day(rain_time) :
    if rain_time >= rain_threshold  :
        return True
    return False

def date_settings():
    global  today_date,today_mm,today_dd,today_yy,today_datetime,today_hh,today_yymmddhh

    today_datetime = datetime.datetime.today()   # datetime 型
    today_date = datetime.date.today()           # date 型
    today_mm = today_date.month
    today_dd = today_date.day
    today_yy = today_date.year - 2000
    today_hh = today_datetime.hour
    today_yymmddhh = today_yy * 1000000 +  today_mm * 10000 + today_dd * 100 + today_hh 


def output_current_date(line) :
    date_str = today_datetime.strftime("%m/%d(%a) %H:%M:%S ")
    s = line.replace("%today%",date_str)
    out.write(s)

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%hour_forecast%" in line :
            hour_forecast()
            continue
        if "%week_forecast%" in line :
            week_forecast()
            continue
        if "%week_hit_rate1%" in line :
            output_week_hit_rate(1)
            continue
        if "%week_hit_rate2%" in line :
            output_week_hit_rate(2)
            continue
        if "%output_hit_rate1%" in line :
            output_hit_rate(1)
            continue
        if "%output_hit_rate2%" in line :
            output_hit_rate(2)
            continue
        if "%output_hit_rate3%" in line :
            output_hit_rate(3)
            continue
        if "%daily_hit_rate1%" in line :
            daily_hit_rate(1)
            continue
        if "%daily_hit_rate2%" in line :
            daily_hit_rate(2)
            continue
        if "%tempera_graph%" in line :
            tempera.tempera_graph(out)
            continue
        if "%tempera_graph_daily%" in line :
            tempera.tempera_graph_daily(out)
            continue
        if "%tempera_graph_week%" in line :
            tempera.tempera_graph_week(out)
            continue
        if "%daily_tempera1%" in line :
            tempera.temperature_info(out,1)
            continue
        if "%daily_tempera2%" in line :
            tempera.temperature_info(out,2)
            continue
        if "%min_max_temperature%" in line :
            tempera.min_max_temperature(out)
            continue
        if "%min_max_temperature_30days%" in line :
            tempera.min_max_temperature_30days(out)
            continue
        if "%monthly_tempera%" in line :
            tempera.monthly_tempera(out)
            continue
        if "%ranking_ave_tempera%" in line :
            tempera.ranking_ave_tempera(out)
            continue
        if "%ranking_max_tempera%" in line :
            tempera.ranking_max_tempera(out)
            continue
        if "%ranking_min_tempera%" in line :
            tempera.ranking_min_tempera(out)
            continue
        if "%ranking_diff_top%" in line :
            tempera.ranking_diff_top(out)
            continue
        if "%ranking_diff_low%" in line :
            tempera.ranking_diff_low(out)
            continue
        if "%tempera_week%" in line :
            tempera.output_tempera_week(out)
            continue
        if "%tempera_week_diff%" in line :
            tempera.output_tempera_week_diff(out)
            continue
        if "%weekly_tempera_table%" in line :
            tempera.weekly_tempera_table(out)
            continue
        if "%week_rain_time_graph%" in line :
            rain.week_rain_time_graph(out)
            continue
        if "%monthly_rain_time%" in line :
            rain.monthly_rain_time(out)
            continue
        if "%daily_precipitation1%" in line :
            rain.daily_precipitation(out,1)
            continue
        if "%daily_precipitation2%" in line :
            rain.daily_precipitation(out,2)
            continue
        if "%continuous_rain%" in line :
            rain.continuous_rain(out)
            continue
        if "%continuous_fine%" in line :
            rain.continuous_fine(out)
            continue
        if "%cur_continuous%" in line :
            rain.cur_continuous(out)
            continue
        if "%top_continuous_rain%" in line :
            rain.top_continuous_rain(out)
            continue
        if "%top_continuous_fine%" in line :
            rain.top_continuous_fine(out)
            continue
        # if "%week_tempera%" in line :
        #     week_tempera()
        #     continue
        if "%version%" in line :
            s = line.replace("%version%",version)
            out.write(s)
            continue
        if "%today%" in line :
            output_current_date(line)
            continue
        out.write(line)

    f.close()
    out.close()

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

def ftp_upload() : 
    if debug == 1 :
        return 
    with FTP_TLS(host=ftp_host, user=ftp_user, passwd=ftp_pass) as ftp:
        ftp.storbinary('STOR {}'.format(ftp_url), open(resultfile, 'rb'))

# -------------------------------------------------------------
main_proc()
