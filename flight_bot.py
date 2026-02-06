import requests
import json
import os
from datetime import datetime

# 從 GitHub Secrets 讀取（唔使 hardcode）
TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY = os.getenv('SERPAPI_KEY')
CHAT_ID = os.getenv('CHAT_ID')

HISTORY_FILE = 'prices.json'  # 會自動喺 repo 儲存，但 Actions 每次新環境，所以用簡單方式

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

def load_prev():
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'hx': None, 'uo': None}

def save(hx, uo):
    with open(HISTORY_FILE, 'w') as f:
        json.dump({'hx': hx, 'uo': uo}, f)

def get_prices():
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_flights",
        "departure_id": "HKG",
        "arrival_id": "TPE",
        "outbound_date": "2026-03-20",
        "return_date": "2026-03-22",
        "adults": 1,
        "currency": "HKD",
        "hl": "zh-Hant",
        "gl": "hk",
        "include_airlines": "HX,UO",
        "api_key": API_KEY
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None, None, None, None

    data = r.json()
    hx_price = hx_times = uo_price = uo_times = None

    for g in data.get('best_flights', []) + data.get('other_flights', []):
        if 'flights' not in g or len(g['flights']) != 2: continue
        out = g['flights'][0]
        ret = g['flights'][1]
        out_num = out.get('flight_number', '')
        ret_num = ret.get('flight_number', '')

        if '252' in out_num and '261' in ret_num:
            hx_price = g.get('price')
            hx_times = f"去程: {out['departure_airport']['time']} → {out['arrival_airport']['time']}\n回程: {ret['departure_airport']['time']} → {ret['arrival_airport']['time']}"
        elif '110' in out_num and '115' in ret_num:
            uo_price = g.get('price')
            uo_times = f"去程: {out['departure_airport']['time']} → {out['arrival_airport']['time']}\n回程: {ret['departure_airport']['time']} → {ret['arrival_airport']['time']}"

    return hx_price, hx_times, uo_price, uo_times

hx_p, hx_t, uo_p, uo_t = get_prices()
prev = load_prev()

msg = f"<b>今日更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')} HKT)</b>\nHKG ↔ TPE 來回 2026-03-20 出發 / 03-22 返程\n經濟艙 單人來回總價\n\n"

if hx_p:
    change = ""
    if prev['hx']:
        try:
            curr = float(hx_p.replace('HKD', '').replace(',', '').strip())
            pre = float(prev['hx'].replace('HKD', '').replace(',', '').strip())
            diff = curr - pre
            change = f" (變化 {'+' if diff>0 else ''}{diff:.0f})"
        except:
            change = ""
    msg += f"<b>香港航空 (超值飛) HX252/HX261:</b>\n{hx_t or '時間未知'}\n{hx_p}{change}\n\n"
else:
    msg += "香港航空：暫無匹配數據\n\n"

if uo_p:
    change = ""
    if prev['uo']:
        try:
            curr = float(uo_p.replace('HKD', '').replace(',', '').strip())
            pre = float(prev['uo'].replace('HKD', '').replace(',', '').strip())
            diff = curr - pre
            change = f" (變化 {'+' if diff>0 else ''}{diff:.0f})"
        except:
            change = ""
    msg += f"<b>香港快運 (隨心飛) UO110/UO115:</b>\n{uo_t or '時間未知'}\n{uo_p}{change}\n\n"
else:
    msg += "香港快運：暫無匹配數據\n"

msg += "價格來自 Google Flights，實際以官網為準。時間為預定，可能有變。"

send_msg(msg)
