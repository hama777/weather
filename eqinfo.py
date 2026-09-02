import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# 26/09/02 v0.04 データをデータフレームの形式にした
version = "0.04"

appdir = os.path.dirname(os.path.abspath(__file__))
conffile = appdir + "/eqinfo.conf"
eqdatafile = appdir + "/eqdata.txt"
templatefile = appdir + "./eq_templ.htm"
resultfile = appdir + "./eqinfo.htm"

URL = "https://typhoon.yahoo.co.jp/weather/jp/earthquake/list/"

headers = {
    "User-Agent": "Mozilla/5.0"
}
new_earthquakes = []
df_eq = ""
def main_proc() :
    global new_earthquakes,df_eq

    read_config()
    read_eqdata()
    if not proxy == "noproxy" :
        os.environ['https_proxy'] = proxy

    response = requests.get(URL,  headers=headers,verify=False)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 地震情報のテーブルを探す
    table = soup.find("table")

    # 表の行を取得
    rows = table.find_all("tr")

    new_list = []
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

        entry = {}
        entry["eqtime"] = occurred_at
        entry["place"] = data[1]
        entry["magnitude"] = data[2]
        entry["scale"] = data[3]

        # --------------------------------------------------
        # 既存データと同じ地震か確認
        # 発生時刻・震源地・マグニチュードの3項目で判定
        # --------------------------------------------------
        is_duplicate = any(
            eq["eqtime"] == entry["eqtime"]
            and eq["place"] == entry["place"]
            and eq["magnitude"] == entry["magnitude"]
            for eq in eq_list
        )

        if is_duplicate:
            # 既存データに到達したので取得終了
            break

        # 新しい地震
        new_list.append(entry)


    # 表示
    for earthquake in new_list:
        etimte = earthquake["eqtime"]
        place = earthquake["place"]
        magnitude = earthquake["magnitude"]
        scale = earthquake["scale"]
        #print(f'{etimte} | {place} \t|{magnitude}|{scale}')

    eq_list.extend(new_list)

    eq_list.sort(
        key=lambda eq: eq["eqtime"],
        reverse=False
    )

    df_eq = pd.DataFrame(eq_list)

    df_eq["eqtime"] = pd.to_datetime(df_eq["eqtime"])
    df_eq["magnitude"] = pd.to_numeric(df_eq["magnitude"], errors="coerce")

    df_eq = df_eq.astype({
        "place": "str",
        "scale": "str",
    })

    # --------------------------------------------------
    # eqdata.txt を新しく書き出す
    # --------------------------------------------------
    with open(eqdatafile, "w", encoding="utf-8") as f:
        for eq in eq_list:
            f.write(
                f"{eq['eqtime'].strftime('%y/%m/%d %H:%M')}\t"
                f"{eq['place']}\t"
                f"{eq['magnitude']}\t"
                f"{eq['scale']}\n"
            )

    parse_template()

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

    if os.path.exists(eqdatafile):
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
