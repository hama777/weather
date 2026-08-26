import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 26/08/26 v0.00 地震情報
version = "0.00"

appdir = os.path.dirname(os.path.abspath(__file__))
conffile = appdir + "/eqinfo.conf"

URL = "https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

def main_proc() :
    read_config()
    if not proxy == "noproxy" :
        os.environ['https_proxy'] = proxy

    response = requests.get(URL,  headers=headers,verify=False)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 地震情報のテーブルを探す
    table = soup.find("table")

    # 表の行を取得
    rows = table.find_all("tr")

    earthquakes = []

    for row in rows:
        cells = row.find_all(["th", "td"])

        if len(cells) != 4:
            continue

        # 各セルの文字列を取得
        data = [cell.get_text(" ", strip=True) for cell in cells]

        # ヘッダー行を除外
        if data[0] == "発生時刻":
            continue

        date_str = data[0].replace("ごろ", "")
        occurred_at = datetime.strptime(date_str, "%Y年%m月%d日 %H時%M分")

        earthquakes.append({
            "eqtime": occurred_at,
            "place": data[1],
            "magnitude": data[2],
            "scale": data[3],
        })

    # 表示
    for earthquake in earthquakes:
        etimte = earthquake["eqtime"]
        place = earthquake["place"]
        magnitude = earthquake["magnitude"]
        scale = earthquake["scale"]
        print(f'{etimte} | {place} \t|{magnitude}|{scale}')

def read_config() : 
    global target_url,proxy,debug,ftp_host,ftp_user,ftp_pass,ftp_url
    if not os.path.isfile(conffile) :
        debug = 1 
        return

    conf = open(conffile,'r', encoding='utf-8')
    proxy  = conf.readline().strip()
    debug = int(conf.readline().strip())
    conf.close()

#-----------------------------------
main_proc()
