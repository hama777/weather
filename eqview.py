import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
#from datetime import date,timedelta
from datetime import datetime, date, timedelta
from ftplib import FTP_TLS

# 26/10/05 v0.10 月別発生回数リスト追加
version = "0.10"

appdir = os.path.dirname(os.path.abspath(__file__))
conffile = appdir + "/eqinfo.conf"
eqdatafile = appdir + "/eqdata.txt"
templatefile = appdir + "./eq_templ.htm"
resultfile = appdir + "./eqinfo.htm"


# df_eq    個々の地震データ
#   eqtime  datetime  発生日時
#   magnitude   float  マグニチュード
#   scape    str   震度
#   place    str   場所


#URL = "https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/"

# headers = {
#     "User-Agent": "Mozilla/5.0"
# }
# new_earthquakes = []
df_eq = ""
def main_proc() :
    global df_eq

    date_settings()
    read_config()
    read_eqdata()
    create_dataframe() 
    #output_eqdata()
    count_by_scale()
    count_by_place()
    create_eq_monthly()
    parse_template()
    ftp_upload()

def create_dataframe() :
    global df_eq
    df_eq = pd.DataFrame(eq_list)

    df_eq["eqtime"] = pd.to_datetime(df_eq["eqtime"])
    df_eq["magnitude"] = pd.to_numeric(df_eq["magnitude"], errors="coerce")

    df_eq = df_eq.astype({
        "place": "str",
        "scale": "str",
    })
    create_eq_daily()    #  仮

def create_eq_daily() :
    global df_eq_daily
    # eqtime を日付に変換
    s = df_eq["eqtime"].dt.normalize()

    # 最小日～最大日まで、すべての日付を作成
    all_dates = pd.date_range(s.min(), s.max(), freq="D")

    # 日付ごとの件数を集計し、存在しない日は 0
    df_eq_daily = (
        s.value_counts()
        .reindex(all_dates, fill_value=0)
        .sort_index()
        .rename_axis("eqdate")
        .reset_index(name="count")
    )

    # 型を確認
    df_eq_daily["count"] = df_eq_daily["count"].astype(int)

def create_eq_monthly() :
    global eq_monthly
    eq_monthly = {}

    # 月ごとに処理
    for month, df_month in df_eq.groupby(df_eq["eqtime"].dt.strftime("%y%m")):

        # 月の発生回数
        count = len(df_month)

        # 震度ごとの回数
        scale_count = df_month["scale"].value_counts().astype(int).to_dict()

        # キーを数値にする
        month_key = int(month)

        # [発生回数, 震度ごとの回数辞書]
        eq_monthly[month_key] = [count, scale_count]

    print(eq_monthly)

def daily_graph() :
    for index, row in df_eq_daily.iterrows():
        date_str = row['eqdate'].strftime('%m/%d')
        count = row['count']
        out.write(f"['{date_str}',{count}],") 

def recent_list() :
    for index, row in df_eq.tail(10).iloc[::-1].iterrows():
        etimte = row["eqtime"]
        place = row["place"]
        magnitude = row["magnitude"]
        scale = row["scale"]
        out.write(f'<tr><td>{etimte}</td><td>{place}</td><td align="right">{magnitude}</td><td align="right">{scale}</td></tr>')

def count_by_scale():
    global scale_count
    scale_count =  df_eq["scale"].value_counts().sort_index().to_dict()

def count_by_place():
    global place_count
    place_count =  df_eq["place"].value_counts().to_dict()

def scale_list() :
    n = len(df_eq)
    for k,v in scale_count.items() :
        p = int(v) / n * 100
        out.write(f'<tr><td align="right">{k}</td><td align="right">{v}</td><td align="right">{p:5.2f}</td></tr>')

def place_list() :
    n = len(df_eq)
    i =0 
    for k,v in place_count.items() :
        i += 1
        p = int(v) / n * 100
        out.write(f'<tr><td align="right">{i}</td><td>{k}</td><td align="right">{v}</td><td align="right">{p:5.2f}</td></tr>')
        if i >= 10 :
            break

def monthly_list() :
    for yymm,v  in eq_monthly.items() :
        count = v[0]
        out.write(f'<tr><td >{yymm}</td><td align="right">{count}</td></tr>')

def read_config() : 
    global target_url,proxy,debug,ftp_host,ftp_user,ftp_pass,ftp_url
    if not os.path.isfile(conffile) :
        debug = 1 
        return

    conf = open(conffile,'r', encoding='utf-8')
    proxy  = conf.readline().strip()
    ftp_host = conf.readline().strip()
    ftp_user = conf.readline().strip()
    ftp_pass = conf.readline().strip()
    ftp_url = conf.readline().strip()
    debug = int(conf.readline().strip())
    conf.close()

def date_settings():
    global  today_date,today_mm,today_dd,today_yy,today_datetime,today_hh,today_yymmddhh

    today_datetime = datetime.today()   # datetime 型
    today_date = date.today()           # date 型

def output_current_date(line) :
    date_str = today_datetime.strftime("%m/%d(%a) %H:%M:%S ")
    s = line.replace("%today%",date_str)
    out.write(s)

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%recent_list%" in line :
            recent_list()
            continue
        if "%daily_graph%" in line :
            daily_graph()
            continue
        if "%scale_list%" in line :
            scale_list()
            continue
        if "%place_list%" in line :
            place_list()
            continue
        if "%monthly_list%" in line :
            monthly_list()
            continue
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

# --------------------------------------------------
# eqdata.txt を読み込む
# --------------------------------------------------
def read_eqdata() :
    global eq_list
    eq_list = []

    if not os.path.exists(eqdatafile):
        return
    with open(eqdatafile, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")

            if not line:
                continue

            data = line.split("\t")

            if len(data) != 4:
                continue

            eq_list.append({
                "eqtime": datetime.strptime(data[0], "%y/%m/%d %H:%M"),
                "place": data[1],
                "magnitude": data[2],
                "scale": data[3],
            })

def ftp_upload() : 
    if debug == 1 :
        return 
    with FTP_TLS(host=ftp_host, user=ftp_user, passwd=ftp_pass) as ftp:
        ftp.storbinary('STOR {}'.format(ftp_url), open(resultfile, 'rb'))


#-----------------------------------
main_proc()
