import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# 26/09/08 v0.01 不要箇所削除
version = "0.01"

appdir = os.path.dirname(os.path.abspath(__file__))
conffile = appdir + "/eqinfo.conf"
eqdatafile = appdir + "/eqdata.txt"
templatefile = appdir + "./eq_templ.htm"
resultfile = appdir + "./eqinfo.htm"

#URL = "https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/"

# headers = {
#     "User-Agent": "Mozilla/5.0"
# }
# new_earthquakes = []
df_eq = ""
def main_proc() :
    global df_eq

    read_config()
    read_eqdata()
    create_dataframe() 
    #output_eqdata()
    parse_template()

def create_dataframe() :
    global df_eq
    df_eq = pd.DataFrame(eq_list)

    df_eq["eqtime"] = pd.to_datetime(df_eq["eqtime"])
    df_eq["magnitude"] = pd.to_numeric(df_eq["magnitude"], errors="coerce")

    df_eq = df_eq.astype({
        "place": "str",
        "scale": "str",
    })

# def output_eqdata() :
#     with open(eqdatafile, "w", encoding="utf-8") as f:
#         for eq in eq_list:
#             f.write(
#                 f"{eq['eqtime'].strftime('%y/%m/%d %H:%M')}\t"
#                 f"{eq['place']}\t"
#                 f"{eq['magnitude']}\t"
#                 f"{eq['scale']}\n"
#             )

def recent_list() :
    for index, row in df_eq.tail(10).iloc[::-1].iterrows():
        etimte = row["eqtime"]
        place = row["place"]
        magnitude = row["magnitude"]
        scale = row["scale"]
        out.write(f'<tr><td>{etimte}</td><td>{place}</td><td align="right">{magnitude}</td><td align="right">{scale}</td></tr>')

def read_config() : 
    global target_url,proxy,debug,ftp_host,ftp_user,ftp_pass,ftp_url
    if not os.path.isfile(conffile) :
        debug = 1 
        return

    conf = open(conffile,'r', encoding='utf-8')
    proxy  = conf.readline().strip()
    debug = int(conf.readline().strip())
    conf.close()

def parse_template() :
    global out 
    f = open(templatefile , 'r', encoding='utf-8')
    out = open(resultfile,'w' ,  encoding='utf-8')
    for line in f :
        if "%recent_list%" in line :
            recent_list()
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


#-----------------------------------
main_proc()
