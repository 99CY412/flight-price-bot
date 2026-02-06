import requests
import os
from datetime import datetime

# 從 GitHub Secrets 讀取
TOKEN = os.getenv('TELEGRAM_TOKEN')
API_KEY = os.getenv('SERPAPI_KEY')
CHAT_ID = os.getenv('CHAT_ID')

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'HTML'}
    requests.post(url, data=payload)

def get_one_way_price(departure_id, arrival_id, date, airline_code, flight_num, flight_label):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": date,
        "adults": 1,
        "currency": "HKD",
        "hl": "zh-Hant",
        "gl": "hk",
        "include_airlines": airline_code,
        "type": "2",  # one-way
        "api_key": API_KEY
    }
    r = requests.get(url, params=params)
    if r.status_code != 200:
        return None, None

    data = r.json()
    price = None
    time_str = None

    for g in data.get('best_flights', []) + data.get('other_flights', []):
        if 'flights' not in g or len(g['flights']) != 1: continue
        flight = g['flights'][0]
        num = flight.get('flight_number', '')
        if flight_num in num:
            price = g.get('price')
            time_str = f"{flight_label} (去程/回程): {flight['departure_airport']['time']} {departure_id} → {flight['arrival_airport']['time']} {arrival_id}"
            break

    return price, time_str

# HX 查詢
hx_go_price, hx_go_time = get_one_way_price("HKG", "TPE", "2026-03-20", "HX", "252", "HX252")
hx_ret_price, hx_ret_time = get_one_way_price("TPE", "HKG", "2026-03-22", "HX", "261", "HX261")

hx_total = None
if hx_go_price and hx_ret_price:
    try:
        go_num = float(hx_go_price.replace('HKD', '').replace(',', '').strip())
        ret_num = float(hx_ret_price.replace('HKD', '').replace(',', '').strip())
        hx_total = f"HKD {go_num + ret_num:.0f}"
    except:
        hx_total = "計算失敗"

# UO 查詢（同樣邏輯）
uo_go_price, uo_go_time = get_one_way_price("HKG", "TPE", "2026-03-20", "UO", "110", "UO110")
uo_ret_price, uo_ret_time = get_one_way_price("TPE", "HKG", "2026-03-22", "UO", "115", "UO115")

uo_total = None
if uo_go_price and uo_ret_price:
    try:
        go_num = float(uo_go_price.replace('HKD', '').replace(',', '').strip())
        ret_num = float(uo_ret_price.replace('HKD', '').replace(',', '').strip())
        uo_total = f"HKD {go_num + ret_num:.0f}"
    except:
        uo_total = "計算失敗"

msg = f"<b>今日更新 ({datetime.now().strftime('%Y-%m-%d %H:%M')} HKT)</b>\nHKG ↔ TPE 來回 2026-03-20 出發 / 03-22 返程\n經濟艙 單人來回總價\n\n"

# 香港航空部分
msg += "<b>香港航空 (超值飛)：</b>\n"
msg += f"- {hx_go_time or 'HX252 (去程): 時間未知或無數據'}\n"
msg += f"- {hx_ret_time or 'HX261 (回程): 時間未知或無數據'}\n"
if hx_total:
    msg += f"- 單人來回總價: {hx_total}\n\n"
else:
    msg += "- 暫無 HX252 + HX261 價格數據（可能 fares 未完全 release）\n\n"

# 香港快運部分
msg += "<b>香港快運 (隨心飛)：</b>\n"
msg += f"- {uo_go_time or 'UO110 (去程): 時間未知或無數據'}\n"
msg += f"- {uo_ret_time or 'UO115 (回程): 時間未知或無數據'}\n"
if uo_total:
    msg += f"- 單人來回總價: {uo_total}\n\n"
else:
    msg += "- 暫無 UO110 + UO115 價格數據（可能 fares 未完全 release）\n\n"

msg += "價格來自 Google Flights 單程查詢加總，實際以官網為準。時間為預定，可能有變。"

send_msg(msg)
