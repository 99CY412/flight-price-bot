import requests
import json
import os
from datetime import datetime

# 從 GitHub Secrets 讀取
TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY = os.getenv('SERPAPI_KEY')
CHAT_ID = os.getenv('CHAT_ID')

HISTORY_FILE = 'prices.json'

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
            hx_times = f"{out['departure_airport']['time']} HKG → {out['arrival_airport']['time']} TPE"
            hx_times = f"HX252 (去程): {hx_times}\nHX261 (回程): {ret['departure_airport']['time']} TPE → {ret['arrival_airport']['time']} HKG"
        elif '110' in out_num and '115' in ret_num:
            uo_price = g.get('price')
            uo_times = f"{out['departure_airport']['time']} HKG → {out['arrival_airport']['time']} TPE"
            uo_times = f"UO110 (去程): {uo_times}\nUO115 (回程): {ret['departure_airport']['time']} TPE → {ret['arrival_airport']['time']} HKG"

    return hx_price, hx_times, uo_price, uo_times

hx_p, hx_t, uo_p, uo_t = get_prices()
prev = load_prev()

# 預設時間（如果 API 無返）
hx_default = "HX252 (去程): 09:05 HKG → 10:50 TPE\nHX261 (回程): 19:20 TPE → 21:25 HKG"
uo_default = "UO110 (去程): 11:25 HKG → 13:10 TPE\nUO115 (回程): 17:40 TPE → 19:40 HKG"

msg = f"<b>今日更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')} HKT)</b>\nHKG ↔ TPE 來回 2026-03-20 出發 / 03-22 返程\n經濟艙 單人來回總價\n\n"

# 香港航空
msg += "<b>香港航空 (超值飛)：</b>\n"
msg += f"- {hx_t or hx_default}\n"
if hx_p:
    hx_price_num = float(hx_p.replace('HKD', '').replace(',', '').strip())
    change_str = ""
    if prev['hx']:
        prev_num = float(prev['hx'].replace('HKD', '').replace(',', '').strip())
        diff = hx_price_num - prev_num
        pct = (diff / prev_num) * 100 if prev_num else 0
        change_str = f" (變化 {'+' if diff>0 else ''}{diff:.0f} / {pct:+.1f}%)"
        if diff < -200 or pct < -10:
            change_str += "，可能有優惠！"
    msg += f"- 單人來回總價: {hx_p}{change_str}\n\n"
else:
    msg += "- 暫無匹配數據\n\n"

# 香港快運
msg += "<b>香港快運 (隨心飛)：</b>\n"
msg += f"- {uo_t or uo_default}\n"
if uo_p:
    uo_price_num = float(uo_p.replace('HKD', '').replace(',', '').strip())
    change_str = ""
    if prev['uo']:
        prev_num = float(prev['uo'].replace('HKD', '').replace(',', '').strip())
        diff = uo_price_num - prev_num
        pct = (diff / prev_num) * 100 if prev_num else 0
        change_str = f" (變化 {'+' if diff>0 else ''}{diff:.0f} / {pct:+.1f}%)"
        if diff < -200 or pct < -10:
            change_str += "，可能有優惠！"
    msg += f"- 單人來回總價: {uo_p}{change_str}\n\n"
else:
    msg += "- 暫無匹配數據\n\n"

msg += "價格來自 Google Flights，實際以官網為準。時間為預定，可能有變。"

send_msg(msg)

# 保存當前價格（用於下次比較）
save(hx_p, uo_p)
